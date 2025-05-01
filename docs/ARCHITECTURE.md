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

### AudioProcessor

The `AudioProcessor` manages text-to-speech conversion using the ElevenLabs API. It:

- Selects appropriate voices based on professor characteristics
- Processes lecture text to handle stage directions and special formatting
- Manages audio file storage and organization
- Provides playback capabilities

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
3. AudioProcessor selects an appropriate voice for the professor
4. AudioProcessor converts text to speech and saves the audio file
5. Repository updates the lecture with the audio file path

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

## Deployment Options

The system is designed to be flexible in deployment:

- **Development** - Local SQLite database, directly calling APIs
- **Production** - PostgreSQL database, containerized with Docker
- **Serverless** - Cloud functions with managed database
