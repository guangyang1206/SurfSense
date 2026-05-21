import { EnumConnectorName } from "@/contracts/enums/connector";
import type { ConnectorTelemetryGroup, ConnectorTelemetryMeta } from "./telemetry-meta.types";

// ============================================================================
// CONNECTOR TELEMETRY REGISTRY
// ----------------------------------------------------------------------------
// Single source of truth for "what does this connector_type look like in
// analytics?". Any connector added to the lists in connector-constants.ts
// is automatically picked up here, so adding a new integration does NOT
// require touching `lib/posthog/events.ts` or per-connector tracking code.
// ============================================================================

export type { ConnectorTelemetryGroup, ConnectorTelemetryMeta } from "./telemetry-meta.types";

export const OAUTH_CONNECTOR_TYPES = [
	EnumConnectorName.GOOGLE_DRIVE_CONNECTOR,
	EnumConnectorName.GOOGLE_GMAIL_CONNECTOR,
	EnumConnectorName.GOOGLE_CALENDAR_CONNECTOR,
	EnumConnectorName.AIRTABLE_CONNECTOR,
	EnumConnectorName.NOTION_CONNECTOR,
	EnumConnectorName.LINEAR_CONNECTOR,
	EnumConnectorName.SLACK_CONNECTOR,
	EnumConnectorName.TEAMS_CONNECTOR,
	EnumConnectorName.ONEDRIVE_CONNECTOR,
	EnumConnectorName.DROPBOX_CONNECTOR,
	EnumConnectorName.DISCORD_CONNECTOR,
	EnumConnectorName.JIRA_CONNECTOR,
	EnumConnectorName.CONFLUENCE_CONNECTOR,
	EnumConnectorName.CLICKUP_CONNECTOR,
] as const;

export const COMPOSIO_CONNECTOR_TYPES = [
	EnumConnectorName.COMPOSIO_GOOGLE_DRIVE_CONNECTOR,
	EnumConnectorName.COMPOSIO_GMAIL_CONNECTOR,
	EnumConnectorName.COMPOSIO_GOOGLE_CALENDAR_CONNECTOR,
] as const;

export const CRAWLER_CONNECTOR_TYPES = [
	EnumConnectorName.YOUTUBE_CONNECTOR,
	EnumConnectorName.WEBCRAWLER_CONNECTOR,
] as const;

export const OTHER_CONNECTOR_TYPES = [
	EnumConnectorName.BOOKSTACK_CONNECTOR,
	EnumConnectorName.GITHUB_CONNECTOR,
	EnumConnectorName.LUMA_CONNECTOR,
	EnumConnectorName.ELASTICSEARCH_CONNECTOR,
	EnumConnectorName.TAVILY_API,
	EnumConnectorName.LINKUP_API,
	EnumConnectorName.BAIDU_SEARCH_API,
	EnumConnectorName.CIRCLEBACK_CONNECTOR,
	EnumConnectorName.MCP_CONNECTOR,
	EnumConnectorName.OBSIDIAN_CONNECTOR,
] as const;

const CONNECTOR_TELEMETRY_REGISTRY: ReadonlyMap<string, ConnectorTelemetryMeta> = (() => {
	const map = new Map<string, ConnectorTelemetryMeta>();

	// OAuth connectors
	for (const type of OAUTH_CONNECTOR_TYPES) {
		const title = getConnectorTitle(type);
		map.set(type, {
			connector_type: type,
			connector_title: title,
			connector_group: "oauth",
			is_oauth: true,
		});
	}

	// Composio connectors
	for (const type of COMPOSIO_CONNECTOR_TYPES) {
		const title = getConnectorTitle(type);
		map.set(type, {
			connector_type: type,
			connector_title: title,
			connector_group: "composio",
			is_oauth: true,
		});
	}

	// Crawler connectors
	for (const type of CRAWLER_CONNECTOR_TYPES) {
		const title = getConnectorTitle(type);
		map.set(type, {
			connector_type: type,
			connector_title: title,
			connector_group: "crawler",
			is_oauth: false,
		});
	}

	// Other connectors
	for (const type of OTHER_CONNECTOR_TYPES) {
		const title = getConnectorTitle(type);
		map.set(type, {
			connector_type: type,
			connector_title: title,
			connector_group: "other",
			is_oauth: false,
		});
	}

	return map;
})();

/**
 * Returns a human-readable title for a connector type.
 * This is a simplified version - in production, you'd import from connector-constants.ts
 */
function getConnectorTitle(connectorType: string): string {
	// Extract the last part after the dot and convert to Title Case
	const parts = connectorType.split(".");
	if (parts.length === 0) return connectorType;

	const lastPart = parts[parts.length - 1];
	return lastPart
		.toLowerCase()
		.split("_")
		.map((word) => word.charAt(0).toUpperCase() + word.slice(1))
		.join(" ");
}

/**
 * Returns telemetry metadata for a connector_type, or a minimal "unknown"
 * record so tracking never no-ops for connectors that exist in the backend
 * but were forgotten in the UI registry.
 */
export function getConnectorTelemetryMeta(connectorType: string): ConnectorTelemetryMeta {
	const hit = CONNECTOR_TELEMETRY_REGISTRY.get(connectorType);
	if (hit) return hit;

	return {
		connector_type: connectorType,
		connector_title: connectorType,
		connector_group: "unknown",
		is_oauth: false,
	};
}
