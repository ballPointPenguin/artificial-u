# ArtificialU System Architecture

This document provides an overview of the ArtificialU system architecture, explaining the key components and how they interact.

## System Overview

ArtificialU is designed with a modular architecture that separates concerns into distinct components:

1. **Content Generation Layer** - Creates educational content using the Anthropic Claude API
2. **Audio Processing Layer** - Converts lecture text to speech using the ElevenLabs API
3. **Data Layer** - Manages persistence of professors, courses, lectures, and other entities
4. **User Interface Layer** - Provides interfaces for interacting with the system (CLI and future web interface)

## Key Components

### UniversitySystem

The `UniversitySystem` class acts as the central orchestrator, integrating the other components and providing a unified API for application features. It coordinates the workflow between content generation, audio processing, and data storage.

### ContentGenerator

The `ContentGenerator` handles all interactions with the Anthropic Claude API. It is responsible for:

- Creating professor profiles with consistent personalities
- Generating course topics tailored to professor teaching styles
- Creating engaging lectures that maintain the professor's voice and perspective
- Ensuring continuity between lectures in a series

### Audio Processing Components

The audio processing layer has been modularized into several specialized components:

#### SpeechProcessor

The `SpeechProcessor` prepares text for optimal speech synthesis by:

- Enhancing text with speech markup for pronunciation of technical terms
- Handling mathematical notation and special characters
- Adding discipline-specific enhancements based on professor's department
- Splitting text into appropriately sized chunks for processing

#### VoiceMapper

The `VoiceMapper` matches professor profiles to appropriate ElevenLabs voices:

- Maps professor attributes (gender, accent, age) to ElevenLabs voice categories
- Selects voices based on quality and appropriate characteristics
- Provides fallback mechanisms when ideal voice matches aren't available

#### ElevenLabsClient

The `ElevenLabsClient` provides low-level access to the ElevenLabs API:

- Retrieves available voices and voice details
- Performs text-to-speech conversion
- Handles API authentication, retries, and error handling

#### TTSService

The `TTSService` orchestrates the text-to-speech process by:

- Coordinating between SpeechProcessor, VoiceMapper, and ElevenLabsClient
- Managing audio file storage and organization
- Providing playback capabilities

#### AudioService

The `AudioService` provides high-level audio functionality to the application:

- Creates audio for lectures based on repository data
- Handles storage and playback of audio files
- Provides voice listing and selection capabilities

#### VoiceService

The `VoiceService` integrates voices from ElevenLabs and the database:

- Calls the ElevenLabsClient to get voices
- Searches the database for matching voices
- Updates the database with new voices
- Calls the VoiceMapper to map voices to professors
- Updates the professor with the voice ID

### Repository

The `Repository` implements data persistence using SQLAlchemy with PostgreSQL as the database backend. It:

- Provides CRUD operations for all domain entities
- Manages relationships between entities
- Handles data retrieval and querying
- Ensures data integrity and consistency

### Command-Line Interface

The CLI provides a user-friendly way to interact with the system through the terminal. It offers commands for:

- Creating courses and professors
- Generating lectures
- Converting lectures to audio
- Browsing and playing content

## Data Model

The core domain model consists of these primary entities:

- **Professor** - A virtual faculty member with a unique personality and teaching style
- **Course** - An academic course a series of topics
- **Lecture** - A single class session with content and optional audio
- **Department** - An academic department containing related courses
- **Voice** - Represents an ElevenLabs voice with attributes and mapping to professors

## Workflow Examples

### Creating a New Course

1. User provides course details (title, code, department)
2. System creates or assigns a professor with appropriate expertise
3. ContentGenerator creates course topics
4. Repository stores the course and topics

### Generating a Lecture

1. User selects a course and lecture topic
2. System retrieves course and professor information
3. ContentGenerator creates lecture content in the professor's style
4. Repository stores the lecture text

### Converting a Lecture to Audio

1. User selects a lecture to convert to audio
2. System retrieves lecture content and professor information
3. VoiceMapper selects an appropriate voice for the professor
4. VoiceService updates the professor with the voice ID
5. SpeechProcessor prepares the text for optimal speech conversion
6. TTSService converts text to speech using ElevenLabsClient
7. AudioService stores the audio file and updates the lecture record
8. Repository updates the lecture with the audio URL

## Future Architecture Enhancements

### Web Interface

A planned Flask/FastAPI web application will provide a more user-friendly interface with:

- RESTful API exposing core functionality
- Responsive frontend for course catalog and lecture playback
- User authentication and personalization

### Async Processing

Future enhancements will include:

- Background workers for content and audio generation
- Message queues for task management
- Progress tracking for long-running tasks

### Enhanced Content

Advanced features will include:

- Image generation for professor portraits
- Slide generation based on lecture content
- Video generation with AI avatars
