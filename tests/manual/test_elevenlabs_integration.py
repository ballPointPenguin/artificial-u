#!/usr/bin/env python3
"""
Manual test script for validating the ElevenLabs API integration.

This script tests:
1. Basic API connectivity
2. Voice retrieval functionality
3. Professor voice creation and mapping
4. Text processing and speech generation

Run with:
    ELEVENLABS_API_KEY=your_api_key python tests/manual/test_elevenlabs_integration.py
"""

import argparse
import os
import sys
import time
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add the project root to the Python path
sys.path.append(str(Path(__file__).parent.parent.parent))

# Import project modules
from artificial_u.audio.processor import AudioProcessor
from artificial_u.models.core import Professor, Lecture

# Constants
TEST_AUDIO_PATH = Path("test_audio_output")


def create_test_professors() -> List[Professor]:
    """Create a diverse set of test professor profiles."""
    professors = [
        Professor(
            id="test-cs-prof",
            name="Dr. Alan Turing",
            title="Professor of Computer Science",
            department="Computer Science",
            specialization="Artificial Intelligence",
            background="Pioneering computer scientist with expertise in AI and computational theory",
            teaching_style="Interactive",
            personality="Enthusiastic"
        ),
        Professor(
            id="test-history-prof",
            name="Dr. Eleanor Roosevelt",
            title="Professor of History",
            department="History",
            specialization="Modern Political History",
            background="Distinguished historian specializing in 20th century political movements",
            teaching_style="Lecture-based",
            personality="Thoughtful"
        ),
        Professor(
            id="test-physics-prof",
            name="Dr. Marie Curie",
            title="Professor of Physics",
            department="Physics",
            specialization="Quantum Mechanics",
            background="Nobel Prize-winning physicist with groundbreaking research in radioactivity",
            teaching_style="Research-focused",
            personality="Analytical"
        ),
    ]
    return professors


def create_test_lecture() -> Lecture:
    """Create a sample lecture for testing text-to-speech."""
    return Lecture(
        id="test-lecture-01",
        course_id="CS101",
        title="Introduction to Artificial Intelligence",
        week_number=1,
        order_in_week=1,
        content="""
# Introduction to Artificial Intelligence

*[Professor enters the classroom and greets students]*

Good morning, everyone! Welcome to our first lecture on Artificial Intelligence. I'm Dr. Alan Turing, and I'll be your guide through this fascinating field.

*[Pauses and looks around the room]*

Today, we'll be covering the fundamental concepts of AI, its history, and why it matters in our modern world. Let's begin by defining what we mean by "artificial intelligence."

*[Professor speaks with enthusiasm]*

AI refers to computer systems designed to perform tasks that typically require human intelligence. These include problem-solving, recognizing speech, visual perception, decision-making, and language translation.

*[Writes key points on the board]*

The history of AI is quite interesting. While many consider it a modern field, the concept dates back to ancient myths and stories about artificial beings endowed with intelligence or consciousness.

*[Professor pauses dramatically]*

However, the formal academic field of AI research only began in 1956, at a conference at Dartmouth College. This is where the term "artificial intelligence" was coined.

*[Speaks softly]*

Now, let's consider why AI is so important today...

*[Resume normal tone]*

Any questions so far?
        """,
        generated_at="2025-04-08T16:00:00",
    )


def test_elevenlabs_api_connection(api_key: str) -> bool:
    """
    Test basic connection to ElevenLabs API.
    
    Args:
        api_key: ElevenLabs API key
        
    Returns:
        bool: True if connection successful, False otherwise
    """
    processor = AudioProcessor(api_key=api_key)
    try:
        voices = processor.get_available_voices()
        voice_count = len(voices)
        print(f"? Successfully connected to ElevenLabs API. Found {voice_count} voices.")
        
        # Display subscription info
        subscription = processor.get_user_subscription_info()
        if subscription:
            print(f"? Subscription tier: {subscription.get('tier', 'Unknown')}")
            print(f"? Character limit: {subscription.get('character_limit', 'Unknown')}")
            print(f"? Characters used: {subscription.get('character_count', 'Unknown')}")
            print(f"? Characters available: {subscription.get('available_characters', 'Unknown')}")
            
        return voice_count > 0
    except Exception as e:
        print(f"? Error connecting to ElevenLabs API: {e}")
        return False


def test_voice_creation_mapping(api_key: str) -> bool:
    """
    Test the voice mapping for professor characteristics.
    
    Args:
        api_key: ElevenLabs API key
        
    Returns:
        bool: True if voices were successfully created, False otherwise
    """
    processor = AudioProcessor(api_key=api_key)
    professors = create_test_professors()
    
    print("\n=== Testing Professor Voice Creation and Mapping ===")
    success = True
    
    for professor in professors:
        try:
            print(f"\nCreating voice for {professor.name} in {professor.department}...")
            voice_id = processor.create_professor_voice(professor)
            print(f"? Created voice {voice_id} for {professor.name}")
            
            # Verify voice settings were properly set
            if professor.voice_settings and "voice_id" in professor.voice_settings:
                print(f"? Voice settings correctly stored: {professor.voice_settings}")
            else:
                print(f"? Voice settings not properly stored for {professor.name}")
                success = False
                
            # Verify the voice can be retrieved
            voice = processor.get_voice_for_professor(professor)
            print(f"? Retrieved voice: {voice.voice_id}")
            
        except Exception as e:
            print(f"? Error creating/retrieving voice for {professor.name}: {e}")
            success = False
    
    return success


def test_text_processing(api_key: str) -> bool:
    """
    Test the text processing functionality.
    
    Args:
        api_key: ElevenLabs API key
        
    Returns:
        bool: True if text processing works correctly, False otherwise
    """
    processor = AudioProcessor(api_key=api_key)
    
    print("\n=== Testing Text Processing ===")
    
    test_texts = [
        "[Professor enters the classroom]Good morning, everyone!",
        "This is a [pauses] test of stage directions.",
        "[speaks excitedly]This should have emotional markup![normal voice]",
        "[whispers]This should be quiet.[speaks loudly]This should be loud."
    ]
    
    success = True
    for text in test_texts:
        try:
            processed = processor.process_stage_directions(text)
            print(f"\nOriginal: {text}")
            print(f"Processed: {processed}")
            
            if processed != text:
                print("? Text was successfully processed")
            else:
                print("?? Text wasn't changed by processing")
                
        except Exception as e:
            print(f"? Error processing text: {e}")
            success = False
    
    return success


def test_speech_generation(api_key: str) -> bool:
    """
    Test the text-to-speech functionality.
    
    Args:
        api_key: ElevenLabs API key
        
    Returns:
        bool: True if speech generation works correctly, False otherwise
    """
    processor = AudioProcessor(api_key=api_key, audio_path=str(TEST_AUDIO_PATH))
    TEST_AUDIO_PATH.mkdir(exist_ok=True)
    
    professors = create_test_professors()
    lecture = create_test_lecture()
    
    print("\n=== Testing Speech Generation ===")
    
    success = True
    try:
        # Use the CS professor for our test
        professor = professors[0]
        
        print(f"Generating audio for a sample lecture by {professor.name}...")
        start_time = time.time()
        
        file_path, audio_data = processor.text_to_speech(lecture, professor)
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"? Generated audio in {duration:.2f} seconds")
        print(f"? Audio saved to: {file_path}")
        print(f"? Audio size: {len(audio_data) / 1024:.2f} KB")
        
    except Exception as e:
        print(f"? Error generating speech: {e}")
        success = False
    
    return success


def main():
    parser = argparse.ArgumentParser(description="Test ElevenLabs API integration")
    parser.add_argument("--api-key", "-k", help="ElevenLabs API key")
    parser.add_argument("--skip-audio", "-s", action="store_true", help="Skip audio generation test")
    args = parser.parse_args()
    
    # Get API key from args or environment
    api_key = args.api_key or os.environ.get("ELEVENLABS_API_KEY")
    if not api_key:
        print("? Error: ElevenLabs API key not provided. Use --api-key or set ELEVENLABS_API_KEY environment variable.")
        sys.exit(1)
    
    # Run tests
    print("=== Starting ElevenLabs Integration Tests ===")
    
    # Test 1: API Connection
    if not test_elevenlabs_api_connection(api_key):
        print("? API connection test failed. Stopping further tests.")
        sys.exit(1)
    
    # Test 2: Voice Creation and Mapping
    voice_test_result = test_voice_creation_mapping(api_key)
    print(f"Voice creation and mapping test {'passed ?' if voice_test_result else 'failed ?'}")
    
    # Test 3: Text Processing
    text_test_result = test_text_processing(api_key)
    print(f"Text processing test {'passed ?' if text_test_result else 'failed ?'}")
    
    # Test 4: Speech Generation (optional)
    if not args.skip_audio:
        speech_test_result = test_speech_generation(api_key)
        print(f"Speech generation test {'passed ?' if speech_test_result else 'failed ?'}")
    
    # Summary
    print("\n=== Test Summary ===")
    print(f"API Connection: {'?' if True else '?'}")
    print(f"Voice Creation: {'?' if voice_test_result else '?'}")
    print(f"Text Processing: {'?' if text_test_result else '?'}")
    if not args.skip_audio:
        print(f"Speech Generation: {'?' if speech_test_result else '?'}")
    
    if not all([voice_test_result, text_test_result]):
        print("\n? Some tests failed!")
        sys.exit(1)
    else:
        print("\n? All tests passed!")


if __name__ == "__main__":
    main()
