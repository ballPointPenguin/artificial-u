"""
Manual test for the ElevenLabs voice selection integration.

This script tests the smart voice selection system against the live ElevenLabs API,
allowing manual validation of the voice matching algorithm with real data.

Prerequisites:
1. Install dependencies: pip install -r requirements.txt
2. Get an API key from ElevenLabs

Usage:
    # Run with API key:
    ELEVENLABS_API_KEY=<your_key> python tests/manual/test_voice_selection_live.py

    # Or run with pytest:
    ELEVENLABS_API_KEY=<your_key> pytest tests/manual/test_voice_selection_live.py -v
"""

import os
import sys
import random
import pytest
import time
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

# Add the project root to the Python path if running directly
if __name__ == "__main__":
    sys.path.append(str(Path(__file__).parent.parent.parent))

# Import from the compatibility layer
from artificial_u.integrations.elevenlabs import (
    VoiceSelectionManager,
)
from artificial_u.models.core import Professor

console = Console()

# Check if we have a real API key, not a test one
api_key = os.environ.get("ELEVENLABS_API_KEY")
using_test_key = api_key == "test_elevenlabs_key"

if api_key and not using_test_key:
    console.print("[bold green]Using real ElevenLabs API key[/bold green]")
    console.print(
        "[bold yellow]Warning: This will make real API calls to ElevenLabs![/bold yellow]"
    )
else:
    console.print("[bold red]No real ElevenLabs API key found[/bold red]")
    console.print(
        "This test requires a real API key set in your .env file or environment"
    )

# Skip tests if no real API key in environment
pytestmark = pytest.mark.skipif(
    not api_key or using_test_key,
    reason="Real ELEVENLABS_API_KEY not found in environment (found test key instead)",
)


@pytest.fixture(scope="module")
def voice_manager():
    """Initialize VoiceSelectionManager with API key."""
    return VoiceSelectionManager(api_key=api_key)


@pytest.fixture(scope="module")
def test_professors():
    """Create a diverse set of test professor profiles."""
    return [
        Professor(
            id=1,
            name="Dr. Elizabeth Norton",
            title="Professor of Literature",
            department="English",
            specialization="Victorian Literature",
            background="British literature expert who studied at Oxford. She brings 20 years of experience having taught at Cambridge before joining the faculty.",
            personality="Eloquent and thoughtful",
            teaching_style="Discussion-based with historical context",
        ),
        Professor(
            id=2,
            name="Dr. Michael Johnson",
            title="Professor of Physics",
            department="Physics",
            specialization="Quantum Mechanics",
            background="American physicist who completed his PhD at MIT. He worked at CERN for several years before entering academia.",
            personality="Enthusiastic and detail-oriented",
            teaching_style="Engaging with practical demonstrations",
        ),
        Professor(
            id=3,
            name="Dr. Sophie Dupont",
            title="Professor of Art History",
            department="Fine Arts",
            specialization="Renaissance Art",
            background="French art historian who studied at the Sorbonne in Paris. She has curated exhibitions at the Louvre and specializes in Italian Renaissance paintings.",
            personality="Passionate and expressive",
            teaching_style="Visual and contextual",
        ),
        Professor(
            id=4,
            name="Dr. Raj Patel",
            title="Professor of Computer Science",
            department="Computer Science",
            specialization="Artificial Intelligence",
            background="Computer scientist from Mumbai, India. He earned his PhD from Stanford and previously worked at Google's AI research division.",
            personality="Methodical and forward-thinking",
            teaching_style="Structured with practical examples",
        ),
        Professor(
            id=5,
            name="Dr. Alex Riley",
            title="Professor of Philosophy",
            department="Philosophy",
            specialization="Ethics",
            background="Leading researcher in ethical frameworks with publications in top journals. Joined the faculty after completing a post-doctoral fellowship.",
            personality="Thoughtful and challenging",
            teaching_style="Socratic method",
        ),
        Professor(
            id=6,
            name="Dr. Walter Simmons",
            title="Distinguished Professor of Economics",
            department="Economics",
            specialization="Macroeconomics",
            background="Emeritus faculty member with 40 years of experience. At 72, he has advised multiple governments and central banks throughout his career.",
            personality="Wise and measured",
            teaching_style="Traditional lectures with deep insights",
        ),
        Professor(
            id=7,
            name="Dr. Emma Chen",
            title="Assistant Professor of Psychology",
            department="Psychology",
            specialization="Developmental Psychology",
            background="Recently completed her PhD at 29 and joined the faculty as its youngest member. Her innovative research on early childhood development has already gained recognition.",
            personality="Energetic and innovative",
            teaching_style="Interactive and technology-focused",
        ),
    ]


@pytest.mark.manual
def test_voice_api_connection(voice_manager):
    """Test basic connection to ElevenLabs API and retrieve available voices."""
    console.print("\n[bold green]Testing API Connection[/bold green]")

    # Get a small sample to test connection
    start_time = time.time()
    voices = voice_manager.get_available_voices(page_size=10, refresh=True)
    duration = time.time() - start_time

    # Verify we got a valid response
    assert isinstance(voices, list)
    assert len(voices) > 0

    # Display information about available voices
    console.print(
        f"✓ Connection successful - Retrieved {len(voices)} voices in {duration:.2f} seconds"
    )

    # Display available filters
    filters = voice_manager.list_available_voice_filters()

    console.print("\n[bold]Available Filter Values:[/bold]")
    filter_table = Table()
    filter_table.add_column("Filter", style="cyan")
    filter_table.add_column("Values", style="yellow")

    for filter_name, values in filters.items():
        if len(values) > 10:
            # Show a sample for large lists
            value_str = ", ".join(values[:5]) + f"... and {len(values)-5} more"
        else:
            value_str = ", ".join(values)
        filter_table.add_row(filter_name, value_str)

    console.print(filter_table)


@pytest.mark.manual
def test_shared_vs_default_voices(voice_manager):
    """Compare the shared voice library with the default voices."""
    console.print("\n[bold green]Comparing Voice Sources[/bold green]")

    # Test with the new shared voices API
    start_time = time.time()
    shared_voices = voice_manager.get_available_voices(refresh=True)
    shared_duration = time.time() - start_time

    # Test with direct API client for regular voices
    start_time = time.time()
    try:
        regular_voices_response = voice_manager.client.voices.get_all()
        regular_voices = [
            {"voice_id": v.voice_id, "name": v.name}
            for v in regular_voices_response.voices
        ]
        regular_duration = time.time() - start_time
    except Exception as e:
        console.print(f"[bold red]Error getting regular voices: {e}[/bold red]")
        regular_voices = []
        regular_duration = 0

    console.print(
        f"Shared Voices API: [bold green]{len(shared_voices)} voices[/bold green] retrieved in {shared_duration:.2f} seconds"
    )
    console.print(
        f"Default Voices API: [bold green]{len(regular_voices)} voices[/bold green] retrieved in {regular_duration:.2f} seconds"
    )

    # Display comparison table
    console.print("\n[bold]Voice Source Comparison:[/bold]")

    table = Table(title="Comparing Voice Sources")
    table.add_column("Metric", style="cyan")
    table.add_column("Shared Voices API", style="green")
    table.add_column("Default Voices API", style="yellow")

    table.add_row("Total Voices", str(len(shared_voices)), str(len(regular_voices)))

    # Count by gender
    shared_males = len([v for v in shared_voices if v.get("gender") == "male"])
    shared_females = len([v for v in shared_voices if v.get("gender") == "female"])
    shared_neutral = len([v for v in shared_voices if v.get("gender") == "neutral"])

    # For regular voices, we'd need to extract gender but we'll show as N/A
    table.add_row("Male Voices", str(shared_males), "N/A")
    table.add_row("Female Voices", str(shared_females), "N/A")
    table.add_row("Neutral Voices", str(shared_neutral), "N/A")

    # Count by accent (top 5)
    accent_counts = {}
    for voice in shared_voices:
        accent = voice.get("accent", "unknown")
        accent_counts[accent] = accent_counts.get(accent, 0) + 1

    top_accents = sorted(accent_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    for accent, count in top_accents:
        table.add_row(f"{accent.title()} accent", str(count), "N/A")

    console.print(table)

    # Show sample from each
    console.print("\n[bold]Sample of Shared Voices:[/bold]")
    sample_shared = random.sample(shared_voices, min(5, len(shared_voices)))

    shared_table = Table()
    shared_table.add_column("Name", style="green")
    shared_table.add_column("Gender", style="magenta")
    shared_table.add_column("Accent", style="yellow")
    shared_table.add_column("Age", style="blue")
    shared_table.add_column("Category", style="red")

    for voice in sample_shared:
        shared_table.add_row(
            voice["name"],
            voice.get("gender", "N/A"),
            voice.get("accent", "N/A"),
            voice.get("age", "N/A"),
            voice.get("category", "N/A"),
        )

    console.print(shared_table)


@pytest.mark.manual
def test_extract_professor_characteristics(voice_manager, test_professors):
    """Test extraction of gender, accent, and age from professor profiles."""
    console.print("\n[bold green]Professor Characteristic Extraction:[/bold green]")

    table = Table(title="Extracted Professor Characteristics")
    table.add_column("Professor", style="cyan")
    table.add_column("Gender", style="magenta")
    table.add_column("Accent", style="yellow")
    table.add_column("Age", style="blue")

    for professor in test_professors:
        gender = voice_manager._extract_gender_from_professor(professor)
        accent = voice_manager._extract_accent_from_professor(professor)
        age = voice_manager._extract_age_from_professor(professor)

        table.add_row(professor.name, gender, accent or "Not detected", age)

    console.print(table)


@pytest.mark.manual
def test_voice_matching(voice_manager, test_professors):
    """Test matching professors to appropriate voices."""
    console.print("\n[bold green]Voice Matching Results:[/bold green]")

    table = Table(title="Professor-Voice Matches")
    table.add_column("Professor", style="cyan")
    table.add_column("Matched Voice", style="green")
    table.add_column("Voice Gender", style="magenta")
    table.add_column("Voice Accent", style="yellow")
    table.add_column("Voice Age", style="blue")
    table.add_column("Quality Score", style="red")

    for professor in test_professors:
        try:
            # Get matching voice
            voice = voice_manager.get_voice_for_professor(professor)

            table.add_row(
                professor.name,
                voice["name"],
                voice["gender"],
                voice["accent"],
                voice["age"],
                f"{voice.get('quality_score', 0):.2f}",
            )

            # Store in mapping for consistency check
            if professor.id:
                voice_manager.voice_mapping_db[professor.id] = voice["voice_id"]

        except Exception as e:
            table.add_row(
                professor.name, f"[bold red]Error: {str(e)}[/bold red]", "", "", "", ""
            )

    console.print(table)

    # Test consistency
    console.print("\n[bold]Testing Voice Selection Consistency:[/bold]")
    consistent = True

    for professor in test_professors:
        if professor.id in voice_manager.voice_mapping_db:
            # Get voice again
            voice = voice_manager.get_voice_for_professor(professor)
            if voice["voice_id"] != voice_manager.voice_mapping_db[professor.id]:
                consistent = False
                console.print(
                    f"[bold red]Inconsistency detected for {professor.name}[/bold red]"
                )

    if consistent:
        console.print(
            "[bold green]✓ Voice selection is consistent for all professors[/bold green]"
        )


@pytest.mark.manual
def test_filtering_and_sampling(voice_manager):
    """Test filtering and sampling voices with various criteria."""
    console.print("\n[bold green]Voice Filtering and Sampling:[/bold green]")

    # Test different filter combinations
    filter_tests = [
        {"gender": "female", "accent": "british"},
        {"gender": "male", "age": "old"},
        {"gender": "female", "accent": "american", "age": "young"},
        {"category": "high_quality"},
        {"gender": "male", "accent": "indian"},
        {"gender": "female", "accent": "spanish"},
    ]

    for i, criteria in enumerate(filter_tests):
        start_time = time.time()
        voices = voice_manager.filter_voices(**criteria)
        duration = time.time() - start_time

        criteria_str = ", ".join(f"{k}={v}" for k, v in criteria.items())

        console.print(f"\n[bold]Filter Test {i+1}:[/bold] {criteria_str}")
        console.print(f"Found {len(voices)} matching voices in {duration:.2f} seconds")

        if voices:
            sample_size = min(3, len(voices))
            sampled = voice_manager.sample_voices_by_criteria(
                count=sample_size, **criteria
            )

            table = Table(title=f"Sample of {sample_size} voices")
            table.add_column("Name", style="green")
            table.add_column("Gender", style="magenta")
            table.add_column("Accent", style="yellow")
            table.add_column("Age", style="blue")
            table.add_column("Quality", style="red")

            for voice in sampled:
                table.add_row(
                    voice["name"],
                    voice["gender"],
                    voice["accent"],
                    voice["age"],
                    f"{voice.get('quality_score', 0):.2f}",
                )

            console.print(table)
        else:
            console.print("[yellow]No voices found matching these criteria[/yellow]")


@pytest.mark.manual
def test_fallback_strategies(voice_manager):
    """Test the system's fallback strategies for difficult matches."""
    console.print("\n[bold green]Testing Fallback Strategies:[/bold green]")

    # Create a professor with unusual characteristics
    unusual_prof = Professor(
        id=8,
        name="Dr. Zhang Wei",
        title="Professor of Linguistics",
        department="Linguistics",
        specialization="East Asian Languages",
        background="Chinese linguist specialized in comparative analysis of Mandarin and Japanese. Previously taught at Beijing University.",
        personality="Precise and methodical",
        teaching_style="Structured and analytical",
    )

    # Extract characteristics
    gender = voice_manager._extract_gender_from_professor(unusual_prof)
    accent = voice_manager._extract_accent_from_professor(unusual_prof)
    age = voice_manager._extract_age_from_professor(unusual_prof)

    console.print(
        Panel(
            f"[bold]Unusual Professor Profile:[/bold]\n"
            f"Name: {unusual_prof.name}\n"
            f"Background: {unusual_prof.background}\n\n"
            f"[bold]Extracted Characteristics:[/bold]\n"
            f"Gender: {gender}\n"
            f"Accent: {accent}\n"
            f"Age: {age}",
            title="Test Case",
        )
    )

    # Format accent to match API expectations
    formatted_accent = accent.lower().replace(" ", "_") if accent else None

    # Test each fallback level
    console.print("\n[bold]Testing Fallback Levels:[/bold]")

    # Level 1: All criteria
    criteria1 = (
        {"gender": gender, "accent": formatted_accent, "age": age}
        if formatted_accent
        else {"gender": gender, "age": age}
    )
    level1 = voice_manager.filter_voices(**criteria1)
    console.print(f"Level 1 (All criteria): {len(level1)} voices found")

    # Level 2: Gender + Accent
    criteria2 = (
        {"gender": gender, "accent": formatted_accent}
        if formatted_accent
        else {"gender": gender}
    )
    level2 = voice_manager.filter_voices(**criteria2)
    console.print(f"Level 2 (Gender + Accent): {len(level2)} voices found")

    # Level 3: Just Gender
    level3 = voice_manager.filter_voices(gender=gender)
    console.print(f"Level 3 (Gender only): {len(level3)} voices found")

    # Level 4: Just Accent
    level4 = (
        voice_manager.filter_voices(accent=formatted_accent) if formatted_accent else []
    )
    console.print(f"Level 4 (Accent only): {len(level4)} voices found")

    # Final result
    start_time = time.time()
    voice = voice_manager.get_voice_for_professor(unusual_prof)
    duration = time.time() - start_time

    console.print(
        f"\n[bold]Final Selected Voice:[/bold] (selected in {duration:.2f} seconds)"
    )
    result_table = Table()
    result_table.add_column("Attribute", style="cyan")
    result_table.add_column("Value", style="yellow")

    result_table.add_row("Voice Name", voice["name"])
    result_table.add_row("Voice Gender", voice["gender"])
    result_table.add_row("Voice Accent", voice["accent"])
    result_table.add_row("Voice Age", voice["age"])
    result_table.add_row("Quality Score", f"{voice.get('quality_score', 0):.2f}")
    result_table.add_row("Category", voice["category"])

    console.print(result_table)

    # Determine which fallback level was used
    if level1 and voice["voice_id"] in [v["voice_id"] for v in level1]:
        level_used = "Level 1 (All criteria matched)"
    elif level2 and voice["voice_id"] in [v["voice_id"] for v in level2]:
        level_used = "Level 2 (Gender + Accent matched)"
    elif level3 and voice["voice_id"] in [v["voice_id"] for v in level3]:
        level_used = "Level 3 (Gender only matched)"
    elif level4 and voice["voice_id"] in [v["voice_id"] for v in level4]:
        level_used = "Level 4 (Accent only matched)"
    else:
        level_used = "Level 5 (Default fallback)"

    console.print(f"[bold green]Fallback level used:[/bold green] {level_used}")


@pytest.mark.manual
def test_accent_variety(voice_manager):
    """Test the variety of accents available in the system."""
    console.print("\n[bold green]Testing Accent Variety:[/bold green]")

    # Sample a few accents to test
    test_accents = [
        "american",
        "british",
        "indian",
        "french",
        "german",
        "spanish",
        "australian",
        "japanese",
    ]

    results_table = Table(title="Voice Results by Accent")
    results_table.add_column("Accent", style="cyan")
    results_table.add_column("Count", style="green")
    results_table.add_column("Sample Voice", style="yellow")
    results_table.add_column("Gender", style="magenta")

    for accent in test_accents:
        voices = voice_manager.filter_voices(accent=accent)

        if voices:
            sample = random.choice(voices)
            results_table.add_row(
                accent.title(), str(len(voices)), sample["name"], sample["gender"]
            )
        else:
            results_table.add_row(accent.title(), "0", "None found", "")

    console.print(results_table)


if __name__ == "__main__":
    # Run tests manually
    console.print("[bold]Running manual ElevenLabs Voice Selection tests[/bold]")

    # Initialize manager
    voice_manager = VoiceSelectionManager(api_key=api_key)

    # Create test professors
    test_professors = [
        Professor(
            id=1,
            name="Dr. Elizabeth Norton",
            title="Professor of Literature",
            department="English",
            specialization="Victorian Literature",
            background="British literature expert who studied at Oxford. She brings 20 years of experience having taught at Cambridge before joining the faculty.",
            personality="Eloquent and thoughtful",
            teaching_style="Discussion-based with historical context",
        ),
        Professor(
            id=2,
            name="Dr. Michael Johnson",
            title="Professor of Physics",
            department="Physics",
            specialization="Quantum Mechanics",
            background="American physicist who completed his PhD at MIT. He worked at CERN for several years before entering academia.",
            personality="Enthusiastic and detail-oriented",
            teaching_style="Engaging with practical demonstrations",
        ),
        Professor(
            id=3,
            name="Dr. Sophie Dupont",
            title="Professor of Art History",
            department="Fine Arts",
            specialization="Renaissance Art",
            background="French art historian who studied at the Sorbonne in Paris. She has curated exhibitions at the Louvre and specializes in Italian Renaissance paintings.",
            personality="Passionate and expressive",
            teaching_style="Visual and contextual",
        ),
        Professor(
            id=4,
            name="Dr. Raj Patel",
            title="Professor of Computer Science",
            department="Computer Science",
            specialization="Artificial Intelligence",
            background="Computer scientist from Mumbai, India. He earned his PhD from Stanford and previously worked at Google's AI research division.",
            personality="Methodical and forward-thinking",
            teaching_style="Structured with practical examples",
        ),
    ]

    # Run tests
    test_voice_api_connection(voice_manager)
    test_shared_vs_default_voices(voice_manager)
    test_extract_professor_characteristics(voice_manager, test_professors)
    test_voice_matching(voice_manager, test_professors)
    test_filtering_and_sampling(voice_manager)
    test_fallback_strategies(voice_manager)
    test_accent_variety(voice_manager)
