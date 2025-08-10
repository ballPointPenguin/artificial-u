#!/usr/bin/env python3
"""
Demonstration of the prefill feature for Anthropic models.

This script shows how to use the new prefill parameter in the ContentService
to guide Claude's responses by providing an initial assistant message.
"""

import asyncio
import logging

from artificial_u.services.content_service import ContentService

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def demonstrate_prefill():
    """Demonstrate the prefill feature with various examples."""
    content_service = ContentService(logger=logger)

    print("🎯 Prefill Feature Demonstration")
    print("=" * 50)

    # Example 1: Structured Response with XML
    print("\n📋 Example 1: XML Structure Prefill")
    print("-" * 30)

    prompt = """Please create a lecture outline for a topic on "Introduction to Machine Learning"
    that covers the basics for undergraduate students."""

    # Use prefill to ensure the response starts with the desired XML structure
    prefill = "<lecture_outline>"

    try:
        response = await content_service.generate_text(
            prompt=prompt,
            prefill=prefill,
            model="claude-3-5-sonnet-20241022",  # Specify Anthropic model
            temperature=0.3,
        )

        print(f"Prompt: {prompt}")
        print(f"Prefill: {prefill}")
        print(f"Response: {prefill}{response}")

    except Exception as e:
        print(f"Error in Example 1: {e}")

    print("\n" + "=" * 50)

    # Example 2: Consistent Format Prefill
    print("\n📝 Example 2: Consistent Format Prefill")
    print("-" * 30)

    prompt = """Explain the concept of neural networks in simple terms."""

    # Use prefill to ensure consistent formatting
    prefill = "## Neural Networks: A Simple Explanation\n\n### What are Neural Networks?\n"

    try:
        response = await content_service.generate_text(
            prompt=prompt, prefill=prefill, model="claude-3-5-sonnet-20241022", temperature=0.3
        )

        print(f"Prompt: {prompt}")
        print(f"Prefill: {prefill}")
        print(f"Response: {prefill}{response}")

    except Exception as e:
        print(f"Error in Example 2: {e}")

    print("\n" + "=" * 50)

    # Example 3: Role-Playing Prefill
    print("\n🎭 Example 3: Role-Playing Prefill")
    print("-" * 30)

    prompt = """You are Professor Smith, an enthusiastic computer science professor.
    Explain recursion to your students."""

    # Use prefill to establish the character's voice
    prefill = (
        "Well hello there, my brilliant students! *adjusts glasses excitedly* "
        "Today we're going to dive into one of my absolute favorite topics in "
        "computer science - recursion! Now, I know some of you might be thinking"
    )

    try:
        response = await content_service.generate_text(
            prompt=prompt,
            prefill=prefill,
            model="claude-3-5-sonnet-20241022",
            temperature=0.7,  # Higher temperature for more creative responses
        )

        print(f"Prompt: {prompt}")
        print(f"Prefill: {prefill}")
        print(f"Response: {prefill}{response}")

    except Exception as e:
        print(f"Error in Example 3: {e}")

    print("\n" + "=" * 50)
    print("✅ Prefill demonstration completed!")

    # Show what happens with non-Anthropic models
    print("\n⚠️  Non-Anthropic Model Behavior")
    print("-" * 30)

    try:
        # This should show a warning but still work
        response = await content_service.generate_text(
            prompt="Explain quantum computing briefly.",
            prefill="Quantum computing is",
            model="gpt-4",  # OpenAI model
            temperature=0.3,
        )
        print("OpenAI model response (prefill ignored):", response[:100] + "...")

    except Exception as e:
        print(f"Error with OpenAI model: {e}")


if __name__ == "__main__":
    asyncio.run(demonstrate_prefill())
