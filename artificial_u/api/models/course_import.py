"""
Pydantic models for course archive import endpoints.
"""

from typing import Any, Dict, Literal, Optional

from pydantic import BaseModel, Field


class ImportResolutions(BaseModel):
    """Admin decisions for ambiguous parts of an import."""

    course_code: Optional[Literal["replace", "rename", "cancel"]] = Field(
        None, description="What to do if the course code already exists"
    )
    new_code: Optional[str] = Field(None, description="New code when course_code is 'rename'")
    professor: Optional[Literal["reuse", "create"]] = Field(
        None, description="Reuse an existing same-named professor or create a new one"
    )
    professor_id: Optional[int] = Field(None, description="Existing professor to reuse")
    hidden: bool = Field(False, description="Import as hidden regardless of exported status")


class ImportAnalysisResponse(BaseModel):
    """Result of uploading an archive: a staged upload key plus the import plan."""

    upload_key: str = Field(..., description="Pass back to POST /courses/import")
    plan: Dict[str, Any] = Field(..., description="What the archive holds and what collides")


class ImportRequest(BaseModel):
    upload_key: str
    resolutions: ImportResolutions = Field(default_factory=ImportResolutions)
