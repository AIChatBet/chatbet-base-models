"""
Tutorial models for client video tutorials management
"""

from __future__ import annotations

from datetime import datetime, timezone
from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict
from typing import Any, List, Optional
from uuid import uuid4


class TutorialItemDB(BaseModel):
    """Tutorial item stored in DynamoDB array"""

    tutorial_id: str
    s3_key: str
    title: str
    file_name: str
    file_size: int
    file_type: str
    uploaded_at: str

    class Config:
        schema_extra = {
            "example": {
                "tutorial_id": "abc-123-uuid",
                "s3_key": "betvip/tutorials/como-apostar.mp4",
                "title": "Cómo realizar tu primera apuesta",
                "file_name": "como-apostar.mp4",
                "file_size": 15728640,
                "file_type": "video/mp4",
                "uploaded_at": "2026-01-05T14:30:00Z",
            }
        }


# ===========================
# Main Configuration - Array Container
# ===========================
class Tutorials(BaseModel):
    """Configuration containing an array of tutorials (without DynamoDB keys)"""

    model_config = ConfigDict(extra="forbid")

    tutorials: List[TutorialItemDB] = Field(
        default_factory=list,
        description="List of all tutorial videos",
    )

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Array-level validation
    @field_validator("tutorials")
    @classmethod
    def _validate_tutorials(cls, v: List[TutorialItemDB]) -> List[TutorialItemDB]:
        """Validate tutorials array"""
        if len(v) > 100:
            raise ValueError("Maximum 100 tutorials allowed")

        # Check for duplicate tutorial_ids
        ids = [t.tutorial_id for t in v]
        if len(ids) != len(set(ids)):
            raise ValueError("Duplicate tutorial_id found in tutorials array")

        return v

    # Factory method
    @classmethod
    def from_minimal(cls) -> "Tutorials":
        """Create an empty tutorials config"""
        now = datetime.now(timezone.utc)
        return cls(
            tutorials=[],
            created_at=now,
            updated_at=now,
        )

    # Utility methods
    def touch(self) -> None:
        """Update the updated_at timestamp"""
        self.updated_at = datetime.now(timezone.utc)

    def add_tutorial(
        self,
        *,
        s3_key: str,
        title: str,
        file_name: str,
        file_size: int,
        file_type: str,
        tutorial_id: Optional[str] = None,
        uploaded_at: Optional[str] = None,
    ) -> TutorialItemDB:
        """Add a new tutorial to the array"""
        tutorial = TutorialItemDB(
            tutorial_id=tutorial_id or str(uuid4()),
            s3_key=s3_key,
            title=title,
            file_name=file_name,
            file_size=file_size,
            file_type=file_type,
            uploaded_at=uploaded_at or datetime.now(timezone.utc).isoformat(),
        )
        self.tutorials.append(tutorial)
        self.touch()
        return tutorial

    def remove_tutorial(self, tutorial_id: str) -> bool:
        """Remove a tutorial by ID. Returns True if found and removed."""
        for i, tutorial in enumerate(self.tutorials):
            if tutorial.tutorial_id == tutorial_id:
                self.tutorials.pop(i)
                self.touch()
                return True
        return False

    def get_tutorial(self, tutorial_id: str) -> Optional[TutorialItemDB]:
        """Get a tutorial by ID"""
        for tutorial in self.tutorials:
            if tutorial.tutorial_id == tutorial_id:
                return tutorial
        return None

    def to_dynamodb_item(self, *, drop_none: bool = True) -> dict:
        """Serialize to DynamoDB-compatible dict"""
        from enum import Enum

        def ser(x: Any) -> Any:
            if isinstance(x, datetime):
                return x.isoformat()
            if isinstance(x, Enum):
                return x.value
            if isinstance(x, dict):
                out = {k: ser(v) for k, v in x.items()}
                return {k: v for k, v in out.items() if not (drop_none and v is None)}
            if isinstance(x, list):
                return [ser(v) for v in x]
            if hasattr(x, "model_dump"):
                return ser(x.model_dump())
            return x  # primitives

        return ser(self.model_dump())


# ===========================
# DynamoDB Variant
# ===========================
class TutorialsDB(Tutorials):
    """DynamoDB variant with PK/SK"""

    PK: Optional[str] = Field(default=None, description="Partition key")
    SK: Optional[str] = Field(default=None, description="Sort key")

    @classmethod
    def from_minimal(cls, company_id: str) -> "TutorialsDB":
        """Create an empty tutorials config for a company"""
        base = Tutorials.from_minimal()
        return cls(
            **base.model_dump(),
            PK=f"company#{company_id}",
            SK="tutorials",
        )

    @model_validator(mode="after")
    def _ensure_keys(self) -> "TutorialsDB":
        """Ensure PK and SK are set"""
        if not self.PK or not self.SK:
            raise ValueError("PK and SK are required for TutorialsDB")
        return self

    # Inherits all utility methods from Tutorials


class TutorialVideo(BaseModel):
    """Tutorial video model"""

    tutorial_id: Optional[str] = Field(default=None, alias="tutorialId")
    key: str
    title: str
    url: str
    file_name: str = Field(alias="fileName")
    file_size: int = Field(alias="fileSize")
    file_type: str = Field(alias="fileType")
    uploaded_at: Optional[str] = Field(default=None, alias="uploadedAt")

    class Config:
        populate_by_name = True
        schema_extra = {
            "example": {
                "tutorialId": "abc-123-uuid",
                "key": "betvip/tutorials/como-apostar.mp4",
                "title": "Cómo realizar tu primera apuesta",
                "url": "https://s3.amazonaws.com/...",
                "fileName": "como-apostar.mp4",
                "fileSize": 15728640,
                "fileType": "video/mp4",
                "uploadedAt": "2026-01-05T14:30:00Z",
            }
        }


class GetTutorialVideosResponse(BaseModel):
    """Response model for getting tutorial videos"""

    videos: List[TutorialVideo]
    count: int

    class Config:
        schema_extra = {
            "example": {
                "videos": [
                    {
                        "tutorialId": "abc-123",
                        "key": "betvip/tutorials/como-apostar.mp4",
                        "title": "Cómo Apostar",
                        "url": "https://s3.amazonaws.com/...",
                        "fileName": "como-apostar.mp4",
                        "fileSize": 15728640,
                        "fileType": "video/mp4",
                        "uploadedAt": "2026-01-05T14:30:00Z",
                    }
                ],
                "count": 1,
            }
        }


class UploadTutorialVideoResponse(BaseModel):
    """Response model for uploading a tutorial video"""

    success: bool
    message: str
    video_url: str = Field(alias="videoUrl")
    video_key: str = Field(alias="videoKey")
    title: str
    tutorial_id: str = Field(alias="tutorialId")

    class Config:
        populate_by_name = True
        schema_extra = {
            "example": {
                "success": True,
                "message": "Video uploaded successfully",
                "videoUrl": "https://s3.amazonaws.com/...",
                "videoKey": "betvip/tutorials/como-apostar.mp4",
                "title": "Cómo Apostar",
                "tutorialId": "abc-123-uuid",
            }
        }


class DeleteTutorialVideoResponse(BaseModel):
    """Response model for deleting a tutorial video"""

    success: bool
    message: str
    deleted_key: str = Field(alias="deletedKey")
    deleted_tutorial_id: Optional[str] = Field(default=None, alias="deletedTutorialId")

    class Config:
        populate_by_name = True
        schema_extra = {
            "example": {
                "success": True,
                "message": "Video deleted successfully",
                "deletedKey": "betvip/tutorials/como-apostar.mp4",
                "deletedTutorialId": "abc-123-uuid",
            }
        }
