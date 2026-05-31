def get_voice_for_provider(provider: str, speaker_id: int, text: str = "") -> dict | str:
    """
    Get the appropriate voice configuration based on the TTS provider and speaker ID.

    Args:
        provider: The TTS provider (e.g., "openai/tts-1", "vertex_ai/test")
        speaker_id: The ID of the speaker (0-5)
        text: Optional text content to detect language for multilingual TTS

    Returns:
        Voice configuration - string for OpenAI, dict for Vertex AI
    """
    if provider == "local/kokoro":
        # Detect language from text for multilingual support
        lang_code = "a"  # Default to American English
        
        if text:
            # Simple language detection based on Unicode ranges
            # This can be improved with a proper language detection library
            has_chinese = any('\u4e00' <= char <= '\u9fff' for char in text)
            has_japanese = any('\u3040' <= char <= '\u309f' or '\u30a0' <= char <= '\u30ff' for char in text)
            has_korean = any('\uac00' <= char <= '\ud7af' for char in text)
            
            if has_chinese:
                lang_code = "z"  # Chinese
            elif has_japanese:
                lang_code = "j"  # Japanese
            elif has_korean:
                lang_code = "k"  # Korean
        
        # Kokoro voice mapping - https://huggingface.co/hexgrad/Kokoro-82M/tree/main/voices
        # Voice prefixes: a=American, b=British, z=Chinese, j=Japanese, k=Korean
        kokoro_voices = {
            0: "am_adam",  # Default/intro voice (American)
            1: "af_bella",  # First speaker (American)
        }
        
        # Override voice based on detected language
        if lang_code == "z":  # Chinese
            kokoro_voices = {
                0: "zm_yunxi",  # Chinese male voice
                1: "zf_xiaobei",  # Chinese female voice
            }
        elif lang_code == "j":  # Japanese
            kokoro_voices = {
                0: "jf_alpha",  # Japanese female voice
                1: "jm_beta",  # Japanese male voice
            }
        elif lang_code == "k":  # Korean
            kokoro_voices = {
                0: "km_gamma",  # Korean male voice
                1: "kf_delta",  # Korean female voice
            }
        
        return kokoro_voices.get(speaker_id, kokoro_voices[0])

    # Extract provider type from the model string
    provider_type = (
        provider.split("/")[0].lower() if "/" in provider else provider.lower()
    )

    if provider_type == "openai":
        # OpenAI voice mapping - simple string values
        openai_voices = {
            0: "alloy",  # Default/intro voice
            1: "echo",  # First speaker
            2: "fable",  # Second speaker
            3: "onyx",  # Third speaker
            4: "nova",  # Fourth speaker
            5: "shimmer",  # Fifth speaker
        }
        return openai_voices.get(speaker_id, "alloy")

    elif provider_type == "vertex_ai":
        # Vertex AI voice mapping - dict with languageCode and name
        vertex_voices = {
            0: {
                "languageCode": "en-US",
                "name": "en-US-Studio-O",
            },
            1: {
                "languageCode": "en-US",
                "name": "en-US-Studio-M",
            },
            2: {
                "languageCode": "en-UK",
                "name": "en-UK-Studio-A",
            },
            3: {
                "languageCode": "en-UK",
                "name": "en-UK-Studio-B",
            },
            4: {
                "languageCode": "en-AU",
                "name": "en-AU-Studio-A",
            },
            5: {
                "languageCode": "en-AU",
                "name": "en-AU-Studio-B",
            },
        }
        return vertex_voices.get(speaker_id, vertex_voices[0])
    elif provider_type == "azure":
        # OpenAI voice mapping - simple string values
        azure_voices = {
            0: "alloy",  # Default/intro voice
            1: "echo",  # First speaker
            2: "fable",  # Second speaker
            3: "onyx",  # Third speaker
            4: "nova",  # Fourth speaker
            5: "shimmer",  # Fifth speaker
        }
        return azure_voices.get(speaker_id, "alloy")

    else:
        # Default fallback to OpenAI format for unknown providers
        default_voices = {
            0: {},
            1: {},
        }
        return default_voices.get(speaker_id, default_voices[0])
