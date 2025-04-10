#!/usr/bin/env python3
"""
CLI tools for managing ElevenLabs integrations.
"""

import os
import sys
import argparse
import time
from typing import Dict, Any, List

from artificial_u.integrations.elevenlabs import (
    VoiceSelectionManager,
    rebuild_voice_cache,
)


def main():
    """Main CLI entry point for ElevenLabs tools."""
    parser = argparse.ArgumentParser(
        description="ArtificialU ElevenLabs Management Tools"
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Rebuild cache command
    rebuild_parser = subparsers.add_parser(
        "rebuild-cache", help="Rebuild the voice cache"
    )
    rebuild_parser.add_argument(
        "--keep", action="store_true", help="Keep existing cache entries (don't clear)"
    )
    rebuild_parser.add_argument(
        "--api-key", help="ElevenLabs API key (optional, uses env var if not provided)"
    )

    # List voices command
    list_parser = subparsers.add_parser("list-voices", help="List available voices")
    list_parser.add_argument(
        "--gender", choices=["male", "female", "neutral"], help="Filter by gender"
    )
    list_parser.add_argument("--accent", help="Filter by accent")
    list_parser.add_argument(
        "--count", type=int, default=10, help="Number of voices to display"
    )
    list_parser.add_argument(
        "--api-key", help="ElevenLabs API key (optional, uses env var if not provided)"
    )

    # Test voice command
    test_parser = subparsers.add_parser("test-voice", help="Test a specific voice")
    test_parser.add_argument("voice_id", help="Voice ID to test")
    test_parser.add_argument(
        "--text",
        default="Hello, this is a test of the ElevenLabs voice synthesis system.",
        help="Text to synthesize",
    )
    test_parser.add_argument(
        "--model", default="eleven_flash_v2_5", help="Model to use for synthesis"
    )
    test_parser.add_argument(
        "--api-key", help="ElevenLabs API key (optional, uses env var if not provided)"
    )

    args = parser.parse_args()

    # If no command specified, show help
    if not args.command:
        parser.print_help()
        return

    # Handle commands
    if args.command == "rebuild-cache":
        handle_rebuild_cache(args)
    elif args.command == "list-voices":
        handle_list_voices(args)
    elif args.command == "test-voice":
        handle_test_voice(args)


def handle_rebuild_cache(args):
    """Handle the rebuild-cache command."""
    print("Rebuilding voice cache...")
    result = rebuild_voice_cache(api_key=args.api_key, clear_existing=not args.keep)

    print(f"Status: {result['status']}")
    print(f"Cached {result['voices_cached']} voices")
    print(f"Time taken: {result['time_taken']:.2f} seconds")

    if result["errors"]:
        print(f"Encountered {len(result['errors'])} errors:")
        for i, error in enumerate(result["errors"][:5]):  # Show only first 5 errors
            print(f"  {i+1}. {error}")

        if len(result["errors"]) > 5:
            print(f"  ... and {len(result['errors']) - 5} more errors")

    print(f"Cache file: {result.get('cache_file', 'unknown')}")


def handle_list_voices(args):
    """Handle the list-voices command."""
    # Initialize voice manager
    manager = VoiceSelectionManager(api_key=args.api_key)

    # Get voices with filters
    voices = manager.get_available_voices(refresh=False)

    # Apply filters
    filtered_voices = voices

    if args.gender:
        filtered_voices = [v for v in filtered_voices if v.get("gender") == args.gender]

    if args.accent:
        filtered_voices = [v for v in filtered_voices if v.get("accent") == args.accent]

    # Sort by quality score
    filtered_voices = sorted(
        filtered_voices, key=lambda v: v.get("quality_score", 0), reverse=True
    )

    # Limit to requested count
    filtered_voices = filtered_voices[: args.count]

    # Display results
    print(f"Found {len(filtered_voices)} voices:")

    for i, voice in enumerate(filtered_voices):
        print(
            f"\n{i+1}. {voice.get('name', 'Unknown')} ({voice.get('voice_id', 'unknown')})"
        )
        print(f"   Gender: {voice.get('gender', 'unknown')}")
        print(f"   Accent: {voice.get('accent', 'unknown')}")
        print(f"   Age: {voice.get('age', 'unknown')}")
        print(f"   Quality: {voice.get('quality_score', 0):.2f}")
        print(f"   Preview: {voice.get('preview_url', 'N/A')}")


def handle_test_voice(args):
    """Handle the test-voice command."""
    try:
        # Import necessary modules
        import tempfile
        from pathlib import Path
        from elevenlabs.client import ElevenLabs
        from elevenlabs import play

        # Get API key
        api_key = args.api_key or os.environ.get("ELEVENLABS_API_KEY")
        if not api_key:
            print(
                "Error: No ElevenLabs API key provided. Please provide --api-key or set ELEVENLABS_API_KEY environment variable."
            )
            return

        print(f"Testing voice {args.voice_id} with model {args.model}")
        print(f'Generating audio for: "{args.text}"')

        # Initialize client
        client = ElevenLabs(api_key=api_key)

        # Generate audio
        try:
            audio_stream = client.text_to_speech.convert(
                text=args.text,
                voice_id=args.voice_id,
                model_id=args.model,
                voice_settings={"stability": 0.5, "clarity": 0.8, "style": 0.0},
            )

            # Handle result - could be bytes or generator
            if hasattr(audio_stream, "__iter__") and not isinstance(
                audio_stream, bytes
            ):
                # It's a generator, consume it
                audio = b"".join(
                    chunk for chunk in audio_stream if isinstance(chunk, bytes)
                )
            else:
                # It's already bytes
                audio = audio_stream

            # Save to temporary file with timestamp
            filename = f"voice_test_{args.voice_id}_{int(time.time())}.mp3"

            with open(filename, "wb") as f:
                f.write(audio)

            print(f"Saved audio to {filename}")
            print("Playing audio...")

            # Play the audio
            play(audio)

        except Exception as e:
            print(f"API Error: {str(e)}")

    except ImportError as e:
        print(f"Import error: {str(e)}")
        print("Make sure you have the ElevenLabs package installed correctly.")
    except Exception as e:
        print(f"Error testing voice: {str(e)}")


if __name__ == "__main__":
    main()
