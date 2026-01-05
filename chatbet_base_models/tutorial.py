"""
Tutorial models for client video tutorials management
"""

from pydantic import BaseModel, Field
from typing import List, Optional


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


class TutorialsDB(BaseModel):
    """Complete DynamoDB item for client tutorials"""

    PK: str
    SK: str
    tutorials: List[TutorialItemDB]
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    class Config:
        schema_extra = {
            "example": {
                "PK": "company#betvip",
                "SK": "tutorials",
                "tutorials": [
                    {
                        "tutorial_id": "abc-123",
                        "s3_key": "betvip/tutorials/como-apostar.mp4",
                        "title": "Cómo Apostar",
                        "file_name": "como-apostar.mp4",
                        "file_size": 15728640,
                        "file_type": "video/mp4",
                        "uploaded_at": "2026-01-05T14:30:00Z",
                    }
                ],
                "created_at": "2026-01-05T14:30:00Z",
                "updated_at": "2026-01-05T14:30:00Z",
            }
        }


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
