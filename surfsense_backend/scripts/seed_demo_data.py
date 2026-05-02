#!/usr/bin/env python
"""
Seed general demo/test data into the SurfSense database.

Creates one (or more) demo users, each with a populated search space
containing a handful of sample note-type documents.  Useful for first-run
demos, integration tests, and Codespace/sandbox environments.

Usage
-----
Run from the ``surfsense_backend/`` directory (same as seed_surfsense_docs.py):

    python scripts/seed_demo_data.py

Optional CLI flags:
    --users N         Number of demo users to create (default: 1)
    --spaces N        Search spaces per user (default: 1)
    --docs N          Sample documents per space (default: 5)
    --force           Re-seed even if demo data already exists
    --email-prefix P  E-mail prefix for generated users (default: "demo")

Examples
--------
# Minimal single-user seed
python scripts/seed_demo_data.py

# Three users with two spaces each, 8 docs per space
python scripts/seed_demo_data.py --users 3 --spaces 2 --docs 8
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys
import uuid
from pathlib import Path

# ---------------------------------------------------------------------------
# Make sure the package root is importable when called directly
# ---------------------------------------------------------------------------
BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

# --- app imports (after sys.path is set) ---
from sqlalchemy import select

from app.db import (
    Document,
    DocumentStatus,
    DocumentType,
    SearchSpace,
    User,
    async_session_maker,
)
from app.users import get_user_db, get_user_manager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("seed_demo_data")

# ---------------------------------------------------------------------------
# Sample document payloads (plain text notes — no file upload needed)
# ---------------------------------------------------------------------------
SAMPLE_DOCS: list[dict] = [
    {
        "title": "Getting Started with SurfSense",
        "content": (
            "SurfSense is an open-source AI knowledge assistant.  Connect your "
            "data sources (Notion, Google Drive, Gmail, …), upload files, and ask "
            "questions that get cited answers drawn from your own knowledge base."
        ),
    },
    {
        "title": "How to Create a Search Space",
        "content": (
            "A Search Space is an isolated knowledge silo.  Open the dashboard, "
            "click **New Search Space**, give it a name and optional description, "
            "then start adding documents or connectors."
        ),
    },
    {
        "title": "Connecting Google Drive",
        "content": (
            "Navigate to Connectors → Google Drive.  Authenticate with your Google "
            "account, select the folders you want to index, and choose a sync "
            "frequency.  SurfSense will keep your indexed content up to date "
            "automatically."
        ),
    },
    {
        "title": "AI Chat with Citation",
        "content": (
            "Open a search space and type a question in the chat box.  SurfSense "
            "will retrieve the most relevant chunks from your knowledge base and "
            "include inline citations so you always know exactly where each fact "
            "came from."
        ),
    },
    {
        "title": "Podcast Generation Guide",
        "content": (
            "SurfSense can convert any set of documents into a podcast in under "
            "30 seconds.  Select the documents you want, click **Generate Podcast**, "
            "choose a voice style, and download the MP3 when it is ready."
        ),
    },
    {
        "title": "Report Export Formats",
        "content": (
            "Reports can be exported as PDF, Markdown, DOCX, or HTML.  After "
            "generating a report in the chat interface, use the **Export** button "
            "to choose your preferred format."
        ),
    },
    {
        "title": "Team Collaboration Features",
        "content": (
            "Invite teammates to a search space by sharing its invite link from "
            "Settings → Members.  Collaborators can read, comment, and contribute "
            "documents, while owners retain full administrative rights."
        ),
    },
    {
        "title": "Self-Hosting SurfSense with Docker",
        "content": (
            "Clone the repository, copy ``docker/.env.example`` to ``docker/.env``, "
            "fill in your LLM and embedding provider keys, then run "
            "``docker compose -f docker/docker-compose.yml up -d``.  The app will "
            "be available at ``http://localhost:3000``."
        ),
    },
    {
        "title": "Supported LLM Providers",
        "content": (
            "SurfSense integrates with OpenAI, Anthropic Claude, Google Gemini, "
            "Groq, Ollama (local), and any OpenAI-compatible endpoint.  Configure "
            "your provider and model in Settings → LLM Configuration."
        ),
    },
    {
        "title": "Privacy and Data Ownership",
        "content": (
            "All data processed by self-hosted SurfSense stays on your own "
            "infrastructure.  Vector embeddings are stored in your local Qdrant "
            "instance and relational data in your PostgreSQL database.  No data is "
            "ever sent to SurfSense servers."
        ),
    },
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _user_exists(session, email: str) -> User | None:
    result = await session.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def _space_exists(session, name: str, user_id) -> SearchSpace | None:
    result = await session.execute(
        select(SearchSpace).where(
            SearchSpace.name == name,
            SearchSpace.user_id == user_id,
        )
    )
    return result.scalar_one_or_none()


async def _create_demo_user(email: str, password: str) -> User | None:
    """
    Create a demo user via the FastAPI-Users user manager so that
    ``on_after_register`` hooks (default search space creation, etc.) fire.
    Returns the User object, or None if creation fails.
    """
    from app.schemas.users import UserCreate

    async with async_session_maker() as session:
        existing = await _user_exists(session, email)
        if existing:
            logger.info("User %s already exists — skipping creation.", email)
            return existing

    # Use the proper user manager so all registration hooks run
    async with async_session_maker() as session:
        async for user_db in get_user_db(session):
            async for user_manager in get_user_manager(user_db):
                try:
                    user = await user_manager.create(
                        UserCreate(
                            email=email,
                            password=password,
                            is_active=True,
                            is_verified=True,
                            is_superuser=False,
                        ),
                        safe=True,
                    )
                    logger.info("Created demo user: %s (id=%s)", email, user.id)
                    return user
                except Exception as exc:
                    logger.warning("Failed to create user %s: %s", email, exc)
                    return None
    return None  # unreachable; keeps type checker happy


async def _seed_search_space(
    session,
    user: User,
    space_name: str,
    space_description: str,
    doc_count: int,
    force: bool,
) -> None:
    existing = await _space_exists(session, space_name, user.id)

    if existing and not force:
        logger.info(
            "Search space '%s' already exists for %s — skipping.", space_name, user.email
        )
        return

    if existing:
        space = existing
        logger.info("Force-reseeding space '%s' for %s.", space_name, user.email)
    else:
        space = SearchSpace(
            name=space_name,
            description=space_description,
            user_id=user.id,
        )
        session.add(space)
        await session.flush()
        logger.info("Created search space '%s' (id=%s).", space_name, space.id)

    # Insert sample NOTE documents
    docs_to_add = SAMPLE_DOCS[:doc_count]
    added = 0
    for doc_data in docs_to_add:
        # Skip duplicates unless --force
        dup_result = await session.execute(
            select(Document).where(
                Document.title == doc_data["title"],
                Document.search_space_id == space.id,
            )
        )
        existing_doc = dup_result.scalar_one_or_none()
        if existing_doc and not force:
            continue

        if existing_doc and force:
            await session.delete(existing_doc)
            await session.flush()

        doc = Document(
            title=doc_data["title"],
            document_type=DocumentType.NOTE,
            search_space_id=space.id,
            created_by_id=user.id,
            status=DocumentStatus.ready(),
            unique_identifier_hash=f"demo:{space.id}:{doc_data['title']}",
        )
        session.add(doc)
        added += 1

    await session.commit()
    logger.info(
        "Seeded %d/%d documents into '%s'.",
        added,
        doc_count,
        space_name,
    )


async def seed_demo_data(
    num_users: int = 1,
    spaces_per_user: int = 1,
    docs_per_space: int = 5,
    email_prefix: str = "demo",
    force: bool = False,
) -> None:
    """Main seed entry-point.

    Parameters
    ----------
    num_users:
        How many demo users to create.
    spaces_per_user:
        How many search spaces to create for each user.
    docs_per_space:
        How many sample documents to insert per search space (max 10).
    email_prefix:
        The e-mail prefix used when generating user addresses.
    force:
        If *True*, re-seed resources that already exist.
    """
    docs_per_space = min(docs_per_space, len(SAMPLE_DOCS))

    logger.info(
        "Starting demo seed — users=%d  spaces/user=%d  docs/space=%d",
        num_users,
        spaces_per_user,
        docs_per_space,
    )

    for user_idx in range(1, num_users + 1):
        suffix = "" if num_users == 1 else str(user_idx)
        email = f"{email_prefix}{suffix}@surfsense.demo"
        # NOTE: intentionally simple password; this is demo/test data only
        password = "SurfSenseDemo2024!"  # noqa: S105

        user = await _create_demo_user(email, password)
        if user is None:
            logger.error("Could not create or retrieve user %s — skipping.", email)
            continue

        async with async_session_maker() as session:
            user_row = await _user_exists(session, email)
            if user_row is None:
                logger.error("User %s not found in DB after creation.", email)
                continue

            for space_idx in range(1, spaces_per_user + 1):
                space_suffix = "" if spaces_per_user == 1 else f" #{space_idx}"
                if num_users > 1:
                    space_name = f"Demo KB (user {user_idx}{space_suffix})"
                else:
                    space_name = f"Demo Knowledge Base{space_suffix}"

                await _seed_search_space(
                    session,
                    user=user_row,
                    space_name=space_name,
                    space_description="Auto-seeded demo search space for development and testing.",
                    doc_count=docs_per_space,
                    force=force,
                )

    logger.info("Demo seed complete.")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Seed general demo/test data into the SurfSense database.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--users",
        type=int,
        default=1,
        dest="num_users",
        help="Number of demo users to create",
    )
    parser.add_argument(
        "--spaces",
        type=int,
        default=1,
        dest="spaces_per_user",
        help="Search spaces per user",
    )
    parser.add_argument(
        "--docs",
        type=int,
        default=5,
        dest="docs_per_space",
        help=f"Sample documents per space (max {len(SAMPLE_DOCS)})",
    )
    parser.add_argument(
        "--email-prefix",
        type=str,
        default="demo",
        help="E-mail prefix for generated demo users",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-seed even if demo data already exists",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    asyncio.run(
        seed_demo_data(
            num_users=args.num_users,
            spaces_per_user=args.spaces_per_user,
            docs_per_space=args.docs_per_space,
            email_prefix=args.email_prefix,
            force=args.force,
        )
    )
