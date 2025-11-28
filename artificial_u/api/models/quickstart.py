"""
API models for Quickstart wizard resources.
"""

from typing import List, Literal, Optional

from pydantic import BaseModel, Field

# --- Request Models ---


class QuickstartMatchRequest(BaseModel):
    """Request model for matching user query to existing courses."""

    query: str = Field(
        ...,
        min_length=3,
        max_length=1000,
        description="User's description of what they want to learn",
    )


class QuickstartStartRequest(BaseModel):
    """Request model for starting the quickstart course creation flow."""

    query: str = Field(
        ...,
        min_length=3,
        max_length=1000,
        description="User's description of what they want to learn",
    )


class IntroAudioRequest(BaseModel):
    """Request model for generating professor intro audio."""

    professor_id: int = Field(..., description="ID of the professor")
    course_title: str = Field(..., description="Title of the course being taught")


class QuickstartProfessorActionRequest(BaseModel):
    """Request model for professor-related actions in quickstart."""

    professor_id: int = Field(..., description="ID of the professor")
    course_id: int = Field(..., description="ID of the course")


class QuickstartRegenerateProfessorRequest(BaseModel):
    """Request model for regenerating a professor with optional freeform prompt."""

    course_id: int = Field(..., description="ID of the course")
    department_id: int = Field(..., description="ID of the department")
    freeform_prompt: Optional[str] = Field(
        None,
        max_length=2000,
        description="Optional freeform prompt to guide professor regeneration",
    )


class QuickstartFinalizeRequest(BaseModel):
    """Request model for finalizing the quickstart flow and generating content."""

    course_id: int = Field(..., description="ID of the course to finalize")


# --- Response Models ---


class CourseBrief(BaseModel):
    """Brief course information for quickstart matching."""

    id: int
    code: str
    title: str
    description: str
    professor_name: Optional[str] = None
    professor_image_url: Optional[str] = None


class QuickstartMatchResponse(BaseModel):
    """Response model for course matching."""

    action: Literal["SELECT", "GENERATE"] = Field(
        ..., description="Whether existing courses match or new one should be generated"
    )
    matched_courses: List[CourseBrief] = Field(
        default_factory=list, description="List of matching courses (if SELECT)"
    )
    reasoning: str = Field(..., description="Explanation of the matching decision")


class QuickstartStartResponse(BaseModel):
    """Response model for starting quickstart flow."""

    course_id: int = Field(..., description="ID of the created or existing course")
    professor_id: int = Field(..., description="ID of the assigned professor")
    department_id: int = Field(..., description="ID of the department")
    course_title: str = Field(..., description="Title of the course")
    course_code: str = Field(..., description="Code of the course")
    course_description: str = Field(..., description="Description of the course")


class ProfessorDetail(BaseModel):
    """Detailed professor information for quickstart review."""

    id: int
    name: str
    title: str
    specialization: str
    description: Optional[str] = None
    personality: Optional[str] = None
    teaching_style: Optional[str] = None
    background: Optional[str] = None
    gender: Optional[str] = None
    age: Optional[int] = None
    accent: Optional[str] = None
    image_url: Optional[str] = None
    voice_preview_url: Optional[str] = None
    voice_id: Optional[int] = None


class QuickstartProfessorResponse(BaseModel):
    """Response model with professor details for review."""

    professor: ProfessorDetail
    course_id: int
    course_title: str


class IntroAudioResponse(BaseModel):
    """Response model for intro audio generation."""

    audio_data_uri: str = Field(
        ..., description="Base64-encoded audio data URI (data:audio/mp3;base64,...)"
    )
    text: str = Field(..., description="The text that was spoken")


class QuickstartFinalizeResponse(BaseModel):
    """Response model for finalizing quickstart."""

    course_id: int = Field(..., description="ID of the finalized course")
    topics_job_id: int = Field(..., description="Job ID for topic generation")
    message: str = Field(..., description="Status message")


class JobStatus(BaseModel):
    """Status of a background job."""

    id: int
    kind: str
    status: str
