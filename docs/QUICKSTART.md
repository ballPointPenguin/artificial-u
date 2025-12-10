# Quickstart Wizard

The Quickstart feature provides a streamlined, wizard-based interface for creating personalized AI-generated courses. It simplifies the multi-step course creation process into an intuitive two-phase flow.

## Overview

The traditional course creation workflow requires users to:

1. Create a department (or select existing)
2. Generate a professor with attributes
3. Generate a professor image
4. Assign a voice to the professor
5. Create the course with topics
6. Generate lecture content
7. Generate audio for lectures

The Quickstart wizard abstracts this complexity into a simple flow:

1. **Intent**: User describes what they want to learn
2. **Professor**: User reviews and approves the assigned instructor
3. Content generation kicks off automatically

## User Flow

### Phase 1: Intent Step

The user lands on `/quickstart` and sees a simple prompt: "What would you like to learn?"

When they submit their learning goal:

1. The system uses an LLM to match their query against existing published courses
2. If good matches exist, the user sees a list with "Listen Now" buttons to go directly to those courses
3. If no matches (or user clicks "Build Something New"), the system:
   - Generates course metadata (title, code, description, level) via AI
   - Uses "smart selection" to pick or create an appropriate department
   - Generates a professor suited to the course
   - Assigns a voice and enqueues image generation

### Phase 2: Professor Step

The user sees the assigned professor with:

- Portrait image (or placeholder while generating)
- Name, title, specialization
- Teaching style description
- Voice preview button (generates ephemeral intro audio)

Available actions:

- **Use This Teacher**: Accept and proceed to content generation
- **Regenerate**: Generate an entirely new professor (with optional freeform guidance)
- **Change Something**:
  - **Image**: Regenerate just the professor's portrait
  - **Voice**: Reassign a different voice from the voice pool
  - **Details**: Same as Regenerate (full professor regeneration)

### Phase 3: Finalization

When the user accepts the professor:

1. Topic generation job is enqueued
2. First lecture generation is chained to run after topics complete
3. User is redirected to the course detail page
4. Course remains in "hidden" status until explicitly published

## Technical Architecture

### Backend Components

#### API Router (`artificial_u/api/routers/quickstart.py`)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/quickstart/match-courses` | POST | Match user query to existing courses using LLM |
| `/quickstart/start` | POST | Create course with smart selection (sync, may timeout) |
| `/quickstart/start/enqueue` | POST | Enqueue course creation job (async, recommended) |
| `/quickstart/professor/{id}` | GET | Get professor details for review |
| `/quickstart/generate-intro-audio` | POST | Generate ephemeral voice preview |
| `/quickstart/regenerate-professor-image` | POST | Regenerate professor image |
| `/quickstart/reassign-professor-voice` | POST | Assign new voice to professor |
| `/quickstart/regenerate-professor` | POST | Generate new professor entirely |
| `/quickstart/finalize` | POST | Kick off content generation |

**Note:** The `/quickstart/start/enqueue` endpoint is recommended for production deployments
where CloudFront enforces a 30-second timeout. The frontend uses this endpoint and polls
for job completion via `GET /api/v1/jobs/{id}`.

#### Course Selector Service (`artificial_u/services/course_selector_service.py`)

Handles LLM-based course matching:

- Retrieves all published courses with professor names
- Sends to LLM with user's learning goal
- LLM decides: SELECT (return 1-3 matching courses) or GENERATE (signal new course needed)
- Uses `COURSE_GENERATION_MODEL` for AI calls

#### Course Selection Prompt (`artificial_u/prompts/course_selection.py`)

Defines the prompt template for course matching:

- Formats existing courses as XML for LLM context
- Provides decision criteria (relevance, specificity, quality of fit)
- Parses XML response into structured decision

### Frontend Components

#### Page (`web/src/pages/Quickstart.tsx`)

Main wizard container managing:

- State machine for wizard steps
- localStorage persistence for resuming interrupted sessions
- Navigation between steps

#### IntentStep (`web/src/components/quickstart/IntentStep.tsx`)

Phase 1 UI:

- Textarea for learning goal input
- Course matching results display
- "Listen Now" / "Build Something New" actions

#### ProfessorStep (`web/src/components/quickstart/ProfessorStep.tsx`)

Phase 2 UI:

- Professor card with image, details
- Voice preview generation
- Regeneration controls (image, voice, full professor)

#### StepIndicator (`web/src/components/quickstart/StepIndicator.tsx`)

Visual progress indicator showing current step (1 → 2 → 3)

#### Service (`web/src/api/services/quickstart-service.ts`)

API client methods for all quickstart endpoints with appropriate timeouts for generation operations.

### State Management

Wizard state is stored in `localStorage` under `quickstart_state`:

```typescript
interface QuickstartState {
  step: 'intent' | 'professor' | 'complete'
  query: string
  courseId: number | null
  professorId: number | null
  departmentId: number | null
  courseTitle: string
  courseCode: string
  professor: ProfessorDetail | null
}
```

This allows users to resume an interrupted session (browser refresh, navigation away, etc.).

## Authentication & Authorization

- All quickstart endpoints require authentication
- The `creator` role is required to access the wizard
- Asset ownership is verified for professor/course modifications
- Coin costs apply for professor image regeneration and full professor regeneration

## Voice Preview

The intro audio feature generates an ephemeral voice sample:

1. User clicks "Hear Their Voice"
2. Backend generates short intro text: "Hello, my name is [name] and I'll be teaching [course]"
3. ElevenLabs TTS converts to audio
4. Audio returned as base64 data URI (not persisted to S3)
5. Frontend plays audio directly from data URI

## Job System Integration

The quickstart flow creates background jobs for:

- `quickstart_start`: Course creation with AI generation and smart department/professor selection.
  This is the primary entry point, enqueued via `/quickstart/start/enqueue` to avoid CloudFront
  timeouts on the long-running AI operations. The job result contains `course_id`, `professor_id`,
  `department_id`, `course_title`, `course_code`, and `course_description`.
- `generate_professor_image`: When regenerating professor image
- `generate_topics_for_course`: At finalization, with `generate_first_lecture: true` flag

Jobs can be monitored via:

- The Jobs page (`/jobs`)
- Real-time SSE updates on course/topic detail pages
- Polling `GET /api/v1/jobs/{id}` for specific job status

### CloudFront Timeout Considerations

CloudFront enforces a hard 30-second origin response timeout. Any synchronous route that
takes longer will result in a `504 Gateway Timeout`. The quickstart flow addresses this by:

1. Enqueueing the `quickstart_start` job instead of running synchronously
2. Frontend polls for job completion using `waitForJobResult()`
3. Job results are extracted and used to proceed to the next wizard step

This pattern keeps the UI responsive while allowing the AI generation (which can take
1-2 minutes) to complete in the background via the ECS worker.

## Home Page Integration

The home page hero CTA ("Start Learning") links directly to `/quickstart`, making it the primary entry point for new course creation.

## Configuration

Relevant settings in `artificial_u/config/settings.py`:

- `COURSE_GENERATION_MODEL`: Used for course metadata generation and course matching
- `COIN_COST_PROFESSOR_IMAGE`: Coin cost for image regeneration
- `COIN_COST_PROFESSOR_GENERATION`: Coin cost for full professor regeneration

## Future Enhancements

Potential improvements for future versions:

- Lecture preview step before finalization
- Progress tracking during content generation
- Multi-course recommendations with comparison
- Learning path suggestions based on query
