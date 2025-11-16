#!/usr/bin/env python3
"""
Standalone audio normalization script using pydub + pyloudnorm.

This script normalizes audio files to a target loudness (LUFS) using broadcast-quality
loudness normalization. Perfect for testing before integrating into the application.

Usage:
    python scripts/normalize_audio.py input1.mp3 [input2.mp3 ...]
    python scripts/normalize_audio.py --target -18 --output normalized.mp3 input.mp3
    python scripts/normalize_audio.py --concat --output combined.mp3 chunk1.mp3 chunk2.mp3 chunk3.mp3

Examples:
    # Normalize single file (outputs to input_normalized.mp3)
    python scripts/normalize_audio.py lecture_chunk1.mp3

    # Normalize and concat multiple chunks
    python scripts/normalize_audio.py --concat chunk1.mp3 chunk2.mp3 chunk3.mp3

    # Custom target loudness (audiobook style)
    python scripts/normalize_audio.py --target -18 lecture.mp3

Dependencies:
    pip install pydub pyloudnorm numpy

    Note: pydub requires ffmpeg or libav to be installed on your system.
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import List

import numpy as np

try:
    from pydub import AudioSegment
except Exception as e:
    import traceback

    print(f"ERROR: Failed to import pydub: {e}")
    traceback.print_exc()
    print(
        "Hint: Ensure pydub is installed and compatible with your Python version,"
        "and that no local files shadow the 'pydub' module."
    )
    sys.exit(1)

try:
    import pyloudnorm as pyln
except ImportError:
    print("ERROR: pyloudnorm not installed. Run: pip install pyloudnorm")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def normalize_audio_segment(
    audio_segment: AudioSegment,
    target_loudness: float = -16.0,
    filename: str = "unknown",
) -> AudioSegment:
    """
    Normalize an AudioSegment to a target loudness using pyloudnorm.

    Args:
        audio_segment: The audio to normalize
        target_loudness: Target loudness in LUFS (default: -16.0 for podcasts)
        filename: Filename for logging purposes

    Returns:
        Normalized AudioSegment
    """
    logger.info(f"  Normalizing: {filename}")
    logger.info(f"    Sample rate: {audio_segment.frame_rate} Hz")
    logger.info(f"    Channels: {audio_segment.channels}")
    logger.info(f"    Duration: {len(audio_segment) / 1000:.2f}s")

    # Convert AudioSegment to numpy array
    samples = np.array(audio_segment.get_array_of_samples(), dtype=np.float32)

    # Reshape for stereo if needed
    if audio_segment.channels == 2:
        samples = samples.reshape((-1, 2))

    # Normalize samples to [-1.0, 1.0] range
    # AudioSegment uses int16 by default, so divide by max value
    samples = samples / (2**15)

    # Create loudness meter
    meter = pyln.Meter(audio_segment.frame_rate)

    # Measure current loudness
    try:
        current_loudness = meter.integrated_loudness(samples)
        logger.info(f"    Current loudness: {current_loudness:.2f} LUFS")
    except Exception as e:
        logger.warning(f"    Could not measure loudness: {e}")
        logger.warning("    Returning original audio unchanged")
        return audio_segment

    # Check if audio is too quiet (likely silence or noise)
    if current_loudness < -70.0:
        logger.warning(f"    Audio is very quiet ({current_loudness:.2f} LUFS)")
        logger.warning("    Skipping normalization to avoid boosting noise")
        return audio_segment

    # Normalize to target loudness
    try:
        normalized_samples = pyln.normalize.loudness(samples, current_loudness, target_loudness)
        logger.info(f"    Target loudness: {target_loudness:.2f} LUFS")

        # Convert back to int16 range
        normalized_samples = (normalized_samples * (2**15)).astype(np.int16)

        # Flatten if stereo
        if audio_segment.channels == 2:
            normalized_samples = normalized_samples.flatten()

        # Create new AudioSegment from normalized samples
        normalized_audio = AudioSegment(
            normalized_samples.tobytes(),
            frame_rate=audio_segment.frame_rate,
            sample_width=2,  # 16-bit = 2 bytes
            channels=audio_segment.channels,
        )

        logger.info("    ✓ Normalized successfully")
        return normalized_audio

    except Exception as e:
        logger.error(f"    Error during normalization: {e}")
        logger.warning("    Returning original audio")
        return audio_segment


def process_files(
    input_files: List[Path],
    output_file: Path = None,
    target_loudness: float = -16.0,
    concat: bool = False,
    keep_intermediates: bool = False,
) -> None:
    """
    Process one or more audio files with loudness normalization.

    Args:
        input_files: List of input MP3 files
        output_file: Output file path (if None, auto-generate)
        target_loudness: Target loudness in LUFS
        concat: Whether to concatenate multiple files
        keep_intermediates: Keep intermediate normalized files when concatenating
    """
    # Validate input files
    for input_file in input_files:
        if not input_file.exists():
            logger.error(f"File not found: {input_file}")
            sys.exit(1)
        if not input_file.suffix.lower() in [".mp3", ".wav", ".m4a", ".ogg"]:
            logger.warning(f"File may not be supported: {input_file}")

    logger.info(f"Processing {len(input_files)} file(s)")
    logger.info(f"Target loudness: {target_loudness} LUFS")
    logger.info("")

    normalized_segments = []
    intermediate_files = []

    # Process each file
    for i, input_file in enumerate(input_files, 1):
        logger.info(f"[{i}/{len(input_files)}] Loading: {input_file.name}")

        try:
            # Load audio file
            audio = AudioSegment.from_file(str(input_file))

            # Normalize
            normalized = normalize_audio_segment(
                audio, target_loudness=target_loudness, filename=input_file.name
            )

            normalized_segments.append(normalized)

            # Save intermediate file if concatenating or if single file
            if len(input_files) == 1 or keep_intermediates or concat:
                if output_file and len(input_files) == 1:
                    # Single file with explicit output path
                    intermediate_path = output_file
                else:
                    # Generate intermediate filename
                    intermediate_path = input_file.parent / f"{input_file.stem}_normalized.mp3"

                if len(input_files) > 1 and concat:
                    # Mark as intermediate for cleanup
                    intermediate_files.append(intermediate_path)

                if len(input_files) == 1 or keep_intermediates:
                    logger.info(f"  Saving to: {intermediate_path}")
                    normalized.export(str(intermediate_path), format="mp3", bitrate="128k")

            logger.info("")

        except Exception as e:
            logger.error(f"Error processing {input_file.name}: {e}")
            sys.exit(1)

    # Concatenate if requested and multiple files
    if concat and len(normalized_segments) > 1:
        logger.info("Concatenating normalized segments...")

        # Combine all segments
        combined = sum(normalized_segments)
        logger.info(f"  Total duration: {len(combined) / 1000:.2f}s")

        # Determine output filename
        if output_file:
            final_output = output_file
        else:
            # Auto-generate name based on first file
            final_output = input_files[0].parent / f"{input_files[0].stem}_combined.mp3"

        logger.info(f"  Saving to: {final_output}")
        combined.export(str(final_output), format="mp3", bitrate="128k")

        # Clean up intermediate files unless keeping
        if not keep_intermediates:
            logger.info("  Cleaning up intermediate files...")
            for intermediate in intermediate_files:
                if intermediate.exists() and intermediate != final_output:
                    intermediate.unlink()
                    logger.info(f"    Removed: {intermediate.name}")

        logger.info("")
        logger.info(f"✓ Success! Output: {final_output}")

    elif len(normalized_segments) == 1:
        output_path = output_file or (
            input_files[0].parent / f"{input_files[0].stem}_normalized.mp3"
        )
        logger.info(f"✓ Success! Output: {output_path}")

    else:
        logger.info(f"✓ Success! Processed {len(normalized_segments)} files")
        for i, input_file in enumerate(input_files):
            output_path = input_file.parent / f"{input_file.stem}_normalized.mp3"
            logger.info(f"  [{i+1}] {output_path}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Normalize audio files using broadcast-quality loudness normalization",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s input.mp3
  %(prog)s --target -18 audiobook.mp3
  %(prog)s --concat --output lecture.mp3 chunk1.mp3 chunk2.mp3 chunk3.mp3
  %(prog)s --keep-intermediates --concat chunk*.mp3

Target loudness standards:
  -16 LUFS: Podcast standard (Apple Podcasts, Spotify)
  -14 LUFS: YouTube, general streaming
  -18 LUFS: Audiobooks (more conservative)
  -23 LUFS: Broadcast TV (EBU R128)
        """,
    )

    parser.add_argument(
        "input_files",
        nargs="+",
        type=Path,
        help="Input audio file(s) to normalize",
    )

    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Output file path (default: <input>_normalized.mp3 or <input>_combined.mp3)",
    )

    parser.add_argument(
        "-t",
        "--target",
        type=float,
        default=-16.0,
        help="Target loudness in LUFS (default: -16.0 for podcasts)",
    )

    parser.add_argument(
        "-c",
        "--concat",
        action="store_true",
        help="Concatenate multiple files after normalizing",
    )

    parser.add_argument(
        "-k",
        "--keep-intermediates",
        action="store_true",
        help="Keep intermediate normalized files when concatenating",
    )

    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    if args.verbose:
        logger.setLevel(logging.DEBUG)

    # Check for ffmpeg/libav
    try:
        # Try to load a silent audio segment to test if ffmpeg is available
        AudioSegment.silent(duration=1)
    except Exception:
        logger.error("FFmpeg/libav not found. Please install:")
        logger.error("  macOS: brew install ffmpeg")
        logger.error("  Ubuntu/Debian: sudo apt-get install ffmpeg")
        logger.error("  Windows: Download from https://ffmpeg.org/download.html")
        sys.exit(1)

    # Process files
    process_files(
        input_files=args.input_files,
        output_file=args.output,
        target_loudness=args.target,
        concat=args.concat,
        keep_intermediates=args.keep_intermediates,
    )


if __name__ == "__main__":
    main()
