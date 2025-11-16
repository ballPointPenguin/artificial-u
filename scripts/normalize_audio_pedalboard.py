#!/usr/bin/env python3
"""
Standalone audio normalization script using Spotify's pedalboard library.

This script applies professional-grade compression, limiting, and gain to normalize
audio without clipping. Perfect for handling audio with sharp peaks.

The processing chain:
1. Compressor - Smooths out dynamic range, tames peaks
2. Limiter - Hard ceiling to prevent clipping
3. Gain - Adjusts overall level to target

Usage:
    python scripts/normalize_audio_pedalboard.py input1.mp3 [input2.mp3 ...]
    python scripts/normalize_audio_pedalboard.py --output normalized.mp3 input.mp3
    python scripts/normalize_audio_pedalboard.py --concat --output combined.mp3 chunk1.mp3 chunk2.mp3

Examples:
    # Normalize single file with default settings
    python scripts/normalize_audio_pedalboard.py lecture_chunk1.mp3

    # Normalize and concat multiple chunks
    python scripts/normalize_audio_pedalboard.py --concat chunk1.mp3 chunk2.mp3 chunk3.mp3

    # Aggressive compression for very dynamic audio
    python scripts/normalize_audio_pedalboard.py --ratio 4.0 --threshold -25 lecture.mp3

    # Gentle processing (less compression)
    python scripts/normalize_audio_pedalboard.py --ratio 2.0 --threshold -15 lecture.mp3

Dependencies:
    pip install pedalboard soundfile numpy

Note: pedalboard is Spotify's audio processing library with VST-quality effects.
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import List, Tuple

import numpy as np

try:
    import soundfile as sf
except ImportError:
    print("ERROR: soundfile not installed. Run: pip install soundfile")
    sys.exit(1)

try:
    from pedalboard import Pedalboard, Compressor, Limiter, Gain
except ImportError:
    print("ERROR: pedalboard not installed. Run: pip install pedalboard")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def calculate_rms_db(audio: np.ndarray) -> float:
    """Calculate RMS level in dB."""
    rms = np.sqrt(np.mean(audio**2))
    if rms > 0:
        return 20 * np.log10(rms)
    return -np.inf


def calculate_peak_db(audio: np.ndarray) -> float:
    """Calculate peak level in dB."""
    peak = np.max(np.abs(audio))
    if peak > 0:
        return 20 * np.log10(peak)
    return -np.inf


def process_audio(
    audio: np.ndarray,
    sample_rate: int,
    target_db: float = -16.0,
    threshold_db: float = -20.0,
    ratio: float = 3.0,
    attack_ms: float = 5.0,
    release_ms: float = 50.0,
    filename: str = "unknown",
) -> np.ndarray:
    """
    Process audio with compression, limiting, and gain normalization.

    Args:
        audio: Audio samples (numpy array)
        sample_rate: Sample rate in Hz
        target_db: Target RMS level in dB (default: -16.0)
        threshold_db: Compressor threshold in dB (default: -20.0)
        ratio: Compression ratio (default: 3.0)
        attack_ms: Compressor attack time in ms (default: 5.0)
        release_ms: Compressor release time in ms (default: 50.0)
        filename: Filename for logging

    Returns:
        Processed audio samples
    """
    logger.info(f"  Processing: {filename}")

    # Calculate input levels
    input_rms_db = calculate_rms_db(audio)
    input_peak_db = calculate_peak_db(audio)

    logger.info(f"    Input RMS: {input_rms_db:.2f} dB")
    logger.info(f"    Input peak: {input_peak_db:.2f} dB")

    # Check for silence
    if input_rms_db < -70.0:
        logger.warning(f"    Audio is very quiet ({input_rms_db:.2f} dB)")
        logger.warning("    Skipping processing to avoid boosting noise")
        return audio

    # Create processing chain
    board = Pedalboard([
        # Step 1: Compression - Smooth out dynamics, reduce peak-to-RMS difference
        Compressor(
            threshold_db=threshold_db,
            ratio=ratio,
            attack_ms=attack_ms,
            release_ms=release_ms,
        ),
        # Step 2: Limiter - Hard ceiling at -0.1 dB to prevent any clipping
        Limiter(
            threshold_db=-0.5,  # Slightly below 0 dB for safety
            release_ms=50.0,
        ),
    ])

    logger.info(f"    Compressor: threshold={threshold_db:.1f}dB, ratio={ratio:.1f}:1")
    logger.info(f"    Limiter: threshold=-0.5dB (preventing clipping)")

    # Apply compression and limiting
    processed = board(audio, sample_rate)

    # Calculate levels after compression/limiting
    compressed_rms_db = calculate_rms_db(processed)
    compressed_peak_db = calculate_peak_db(processed)

    logger.info(f"    After compression RMS: {compressed_rms_db:.2f} dB")
    logger.info(f"    After compression peak: {compressed_peak_db:.2f} dB")

    # Calculate gain needed to reach target
    gain_needed_db = target_db - compressed_rms_db

    # Apply gain to reach target level
    if abs(gain_needed_db) > 0.5:  # Only apply if significant change needed
        logger.info(f"    Applying gain: {gain_needed_db:+.2f} dB to reach target {target_db:.1f} dB")

        gain_board = Pedalboard([
            Gain(gain_db=gain_needed_db),
            # Safety limiter after gain
            Limiter(threshold_db=-0.3, release_ms=10.0),
        ])

        processed = gain_board(processed, sample_rate)
    else:
        logger.info(f"    No gain adjustment needed (within 0.5 dB of target)")

    # Calculate final levels
    final_rms_db = calculate_rms_db(processed)
    final_peak_db = calculate_peak_db(processed)

    logger.info(f"    Final RMS: {final_rms_db:.2f} dB (target: {target_db:.1f} dB)")
    logger.info(f"    Final peak: {final_peak_db:.2f} dB")

    # Verify no clipping
    if final_peak_db > -0.1:
        logger.warning(f"    ⚠ Peak is close to 0 dB, may have slight clipping")
    else:
        logger.info(f"    ✓ No clipping detected")

    return processed


def load_audio(file_path: Path) -> Tuple[np.ndarray, int]:
    """Load audio file and return samples + sample rate."""
    logger.info(f"  Loading: {file_path.name}")

    audio, sample_rate = sf.read(str(file_path), always_2d=False)

    # Convert to float32 if needed
    if audio.dtype != np.float32:
        audio = audio.astype(np.float32)

    duration = len(audio) / sample_rate
    channels = 1 if audio.ndim == 1 else audio.shape[1]

    logger.info(f"    Sample rate: {sample_rate} Hz")
    logger.info(f"    Channels: {channels}")
    logger.info(f"    Duration: {duration:.2f}s")

    return audio, sample_rate


def save_audio(audio: np.ndarray, sample_rate: int, file_path: Path) -> None:
    """Save audio to file."""
    logger.info(f"  Saving to: {file_path}")

    # Ensure audio is in correct format
    if audio.dtype != np.float32:
        audio = audio.astype(np.float32)

    # Clip to [-1, 1] range for safety
    audio = np.clip(audio, -1.0, 1.0)

    sf.write(str(file_path), audio, sample_rate, subtype='PCM_16')


def process_files(
    input_files: List[Path],
    output_file: Path = None,
    target_db: float = -16.0,
    threshold_db: float = -20.0,
    ratio: float = 3.0,
    attack_ms: float = 5.0,
    release_ms: float = 50.0,
    concat: bool = False,
    keep_intermediates: bool = False,
) -> None:
    """
    Process one or more audio files with compression and normalization.

    Args:
        input_files: List of input audio files
        output_file: Output file path (if None, auto-generate)
        target_db: Target RMS level in dB
        threshold_db: Compressor threshold in dB
        ratio: Compression ratio
        attack_ms: Compressor attack time
        release_ms: Compressor release time
        concat: Whether to concatenate multiple files
        keep_intermediates: Keep intermediate files when concatenating
    """
    # Validate input files
    for input_file in input_files:
        if not input_file.exists():
            logger.error(f"File not found: {input_file}")
            sys.exit(1)

    logger.info(f"Processing {len(input_files)} file(s)")
    logger.info(f"Target level: {target_db:.1f} dB RMS")
    logger.info("")

    processed_files = []
    processed_audio = []
    common_sample_rate = None

    # Process each file
    for i, input_file in enumerate(input_files, 1):
        logger.info(f"[{i}/{len(input_files)}] {input_file.name}")

        try:
            # Load audio
            audio, sample_rate = load_audio(input_file)

            # Check sample rate consistency for concatenation
            if common_sample_rate is None:
                common_sample_rate = sample_rate
            elif concat and sample_rate != common_sample_rate:
                logger.error(f"  Sample rate mismatch: {sample_rate} != {common_sample_rate}")
                logger.error("  All files must have the same sample rate for concatenation")
                sys.exit(1)

            # Process audio
            processed = process_audio(
                audio,
                sample_rate,
                target_db=target_db,
                threshold_db=threshold_db,
                ratio=ratio,
                attack_ms=attack_ms,
                release_ms=release_ms,
                filename=input_file.name,
            )

            # Save intermediate file if needed
            if len(input_files) == 1 or keep_intermediates or concat:
                if output_file and len(input_files) == 1:
                    intermediate_path = output_file
                else:
                    intermediate_path = input_file.parent / f"{input_file.stem}_normalized.wav"

                if len(input_files) == 1 or keep_intermediates:
                    save_audio(processed, sample_rate, intermediate_path)

                processed_files.append(intermediate_path)

            if concat:
                processed_audio.append(processed)

            logger.info("")

        except Exception as e:
            logger.error(f"Error processing {input_file.name}: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)

    # Concatenate if requested
    if concat and len(processed_audio) > 1:
        logger.info("Concatenating processed segments...")

        # Combine all segments
        combined = np.concatenate(processed_audio)
        total_duration = len(combined) / common_sample_rate

        logger.info(f"  Total duration: {total_duration:.2f}s")

        # Determine output filename
        if output_file:
            final_output = output_file
        else:
            final_output = input_files[0].parent / f"{input_files[0].stem}_combined.wav"

        save_audio(combined, common_sample_rate, final_output)

        # Clean up intermediate files unless keeping
        if not keep_intermediates:
            logger.info("  Cleaning up intermediate files...")
            for intermediate in processed_files:
                if intermediate.exists() and intermediate != final_output:
                    intermediate.unlink()
                    logger.info(f"    Removed: {intermediate.name}")

        logger.info("")
        logger.info(f"✓ Success! Output: {final_output}")

    elif len(processed_audio) == 1:
        output_path = output_file or (input_files[0].parent / f"{input_files[0].stem}_normalized.wav")
        logger.info(f"✓ Success! Output: {output_path}")

    else:
        logger.info(f"✓ Success! Processed {len(input_files)} files")
        for i, input_file in enumerate(input_files):
            output_path = input_file.parent / f"{input_file.stem}_normalized.wav"
            logger.info(f"  [{i+1}] {output_path}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Normalize audio with compression and limiting (no clipping)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s input.mp3
  %(prog)s --concat --output lecture.wav chunk1.mp3 chunk2.mp3 chunk3.mp3
  %(prog)s --ratio 4.0 --threshold -25 dynamic_audio.mp3

Compression settings guide:
  Gentle (preserves dynamics):  --ratio 2.0 --threshold -15
  Moderate (balanced):          --ratio 3.0 --threshold -20  (default)
  Aggressive (very consistent): --ratio 4.0 --threshold -25

Target level guide:
  -16 dB RMS: Podcast/streaming standard (default)
  -18 dB RMS: Audiobook (more conservative)
  -14 dB RMS: YouTube/general streaming (louder)
        """,
    )

    parser.add_argument(
        "input_files",
        nargs="+",
        type=Path,
        help="Input audio file(s) to process",
    )

    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Output file path (default: <input>_normalized.wav)",
    )

    parser.add_argument(
        "-t",
        "--target",
        type=float,
        default=-16.0,
        help="Target RMS level in dB (default: -16.0)",
    )

    parser.add_argument(
        "--threshold",
        type=float,
        default=-20.0,
        help="Compressor threshold in dB (default: -20.0)",
    )

    parser.add_argument(
        "--ratio",
        type=float,
        default=3.0,
        help="Compression ratio (default: 3.0)",
    )

    parser.add_argument(
        "--attack",
        type=float,
        default=5.0,
        help="Compressor attack time in ms (default: 5.0)",
    )

    parser.add_argument(
        "--release",
        type=float,
        default=50.0,
        help="Compressor release time in ms (default: 50.0)",
    )

    parser.add_argument(
        "-c",
        "--concat",
        action="store_true",
        help="Concatenate multiple files after processing",
    )

    parser.add_argument(
        "-k",
        "--keep-intermediates",
        action="store_true",
        help="Keep intermediate files when concatenating",
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

    # Process files
    process_files(
        input_files=args.input_files,
        output_file=args.output,
        target_db=args.target,
        threshold_db=args.threshold,
        ratio=args.ratio,
        attack_ms=args.attack,
        release_ms=args.release,
        concat=args.concat,
        keep_intermediates=args.keep_intermediates,
    )


if __name__ == "__main__":
    main()
