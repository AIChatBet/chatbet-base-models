import pytest

from chatbet_base_models.tutorial import (
    TutorialItemDB,
    TutorialsDB,
    TutorialVideo,
    GetTutorialVideosResponse,
    UploadTutorialVideoResponse,
    DeleteTutorialVideoResponse,
)


class TestTutorialItemDB:
    """Test TutorialItemDB model"""

    def test_create_tutorial_item_db(self):
        """Test creating tutorial item for DynamoDB"""
        item = TutorialItemDB(
            tutorial_id="abc-123-uuid",
            s3_key="betvip/tutorials/como-apostar.mp4",
            title="Cómo realizar tu primera apuesta",
            file_name="como-apostar.mp4",
            file_size=15728640,
            file_type="video/mp4",
            uploaded_at="2026-01-05T14:30:00Z",
        )
        assert item.tutorial_id == "abc-123-uuid"
        assert item.s3_key == "betvip/tutorials/como-apostar.mp4"
        assert item.title == "Cómo realizar tu primera apuesta"
        assert item.file_name == "como-apostar.mp4"
        assert item.file_size == 15728640
        assert item.file_type == "video/mp4"
        assert item.uploaded_at == "2026-01-05T14:30:00Z"

    def test_tutorial_item_db_from_dict(self):
        """Test creating TutorialItemDB from dictionary"""
        data = {
            "tutorial_id": "xyz-789",
            "s3_key": "client/tutorials/test.mp4",
            "title": "Test Tutorial",
            "file_name": "test.mp4",
            "file_size": 5242880,
            "file_type": "video/mp4",
            "uploaded_at": "2026-01-05T10:00:00Z",
        }
        item = TutorialItemDB.model_validate(data)
        assert item.tutorial_id == "xyz-789"
        assert item.s3_key == "client/tutorials/test.mp4"
        assert item.file_size == 5242880

    def test_tutorial_item_db_model_dump(self):
        """Test dumping TutorialItemDB to dictionary"""
        item = TutorialItemDB(
            tutorial_id="test-123",
            s3_key="test/video.mp4",
            title="Test",
            file_name="video.mp4",
            file_size=1024000,
            file_type="video/mp4",
            uploaded_at="2026-01-05T12:00:00Z",
        )
        data = item.model_dump()
        assert data["tutorial_id"] == "test-123"
        assert data["s3_key"] == "test/video.mp4"
        assert data["file_size"] == 1024000


class TestTutorialsDB:
    """Test TutorialsDB model"""

    def test_create_tutorials_db_with_all_fields(self):
        """Test creating TutorialsDB with all fields"""
        tutorials = [
            TutorialItemDB(
                tutorial_id="abc-123",
                s3_key="betvip/tutorials/como-apostar.mp4",
                title="Cómo Apostar",
                file_name="como-apostar.mp4",
                file_size=15728640,
                file_type="video/mp4",
                uploaded_at="2026-01-05T14:30:00Z",
            )
        ]
        db_item = TutorialsDB(
            PK="company#betvip",
            SK="tutorials",
            tutorials=tutorials,
            created_at="2026-01-05T14:30:00Z",
            updated_at="2026-01-05T14:30:00Z",
        )
        assert db_item.PK == "company#betvip"
        assert db_item.SK == "tutorials"
        assert len(db_item.tutorials) == 1
        assert db_item.tutorials[0].tutorial_id == "abc-123"
        assert db_item.created_at == "2026-01-05T14:30:00Z"
        assert db_item.updated_at == "2026-01-05T14:30:00Z"

    def test_create_tutorials_db_with_minimal_fields(self):
        """Test creating TutorialsDB with minimal required fields"""
        db_item = TutorialsDB(
            PK="company#testclient",
            SK="tutorials",
            tutorials=[],
        )
        assert db_item.PK == "company#testclient"
        assert db_item.SK == "tutorials"
        assert len(db_item.tutorials) == 0
        assert db_item.created_at is None
        assert db_item.updated_at is None

    def test_tutorials_db_with_multiple_tutorials(self):
        """Test TutorialsDB with multiple tutorial items"""
        tutorials = [
            TutorialItemDB(
                tutorial_id="abc-123",
                s3_key="client/tutorials/video1.mp4",
                title="Tutorial 1",
                file_name="video1.mp4",
                file_size=10485760,
                file_type="video/mp4",
                uploaded_at="2026-01-05T10:00:00Z",
            ),
            TutorialItemDB(
                tutorial_id="def-456",
                s3_key="client/tutorials/video2.mp4",
                title="Tutorial 2",
                file_name="video2.mp4",
                file_size=20971520,
                file_type="video/mp4",
                uploaded_at="2026-01-05T11:00:00Z",
            ),
            TutorialItemDB(
                tutorial_id="ghi-789",
                s3_key="client/tutorials/video3.mp4",
                title="Tutorial 3",
                file_name="video3.mp4",
                file_size=15728640,
                file_type="video/mp4",
                uploaded_at="2026-01-05T12:00:00Z",
            ),
        ]
        db_item = TutorialsDB(
            PK="company#testclient",
            SK="tutorials",
            tutorials=tutorials,
            created_at="2026-01-05T10:00:00Z",
            updated_at="2026-01-05T12:00:00Z",
        )
        assert len(db_item.tutorials) == 3
        assert db_item.tutorials[0].title == "Tutorial 1"
        assert db_item.tutorials[1].title == "Tutorial 2"
        assert db_item.tutorials[2].title == "Tutorial 3"

    def test_tutorials_db_from_dict(self):
        """Test creating TutorialsDB from dictionary"""
        data = {
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
        db_item = TutorialsDB.model_validate(data)
        assert db_item.PK == "company#betvip"
        assert len(db_item.tutorials) == 1
        assert db_item.tutorials[0].tutorial_id == "abc-123"

    def test_tutorials_db_model_dump(self):
        """Test dumping TutorialsDB to dictionary"""
        tutorials = [
            TutorialItemDB(
                tutorial_id="test-123",
                s3_key="test/video.mp4",
                title="Test",
                file_name="video.mp4",
                file_size=1024000,
                file_type="video/mp4",
                uploaded_at="2026-01-05T12:00:00Z",
            )
        ]
        db_item = TutorialsDB(
            PK="company#test",
            SK="tutorials",
            tutorials=tutorials,
            created_at="2026-01-05T12:00:00Z",
            updated_at="2026-01-05T12:00:00Z",
        )
        data = db_item.model_dump()
        assert data["PK"] == "company#test"
        assert data["SK"] == "tutorials"
        assert len(data["tutorials"]) == 1
        assert data["created_at"] == "2026-01-05T12:00:00Z"


class TestTutorialVideo:
    """Test TutorialVideo model"""

    def test_create_tutorial_video_with_all_fields(self):
        """Test creating tutorial video with all fields"""
        video = TutorialVideo(
            tutorial_id="abc-123-uuid",
            key="betvip/tutorials/como-apostar.mp4",
            title="Cómo realizar tu primera apuesta",
            url="https://s3.amazonaws.com/bucket/video.mp4",
            file_name="como-apostar.mp4",
            file_size=15728640,
            file_type="video/mp4",
            uploaded_at="2026-01-05T14:30:00Z",
        )
        assert video.tutorial_id == "abc-123-uuid"
        assert video.key == "betvip/tutorials/como-apostar.mp4"
        assert video.title == "Cómo realizar tu primera apuesta"
        assert video.url == "https://s3.amazonaws.com/bucket/video.mp4"
        assert video.file_name == "como-apostar.mp4"
        assert video.file_size == 15728640
        assert video.file_type == "video/mp4"
        assert video.uploaded_at == "2026-01-05T14:30:00Z"

    def test_create_tutorial_video_with_minimal_fields(self):
        """Test creating tutorial video with minimal required fields"""
        video = TutorialVideo(
            key="betvip/tutorials/video.mp4",
            title="Tutorial básico",
            url="https://example.com/video.mp4",
            file_name="video.mp4",
            file_size=1024000,
            file_type="video/mp4",
        )
        assert video.tutorial_id is None
        assert video.uploaded_at is None
        assert video.key == "betvip/tutorials/video.mp4"
        assert video.title == "Tutorial básico"

    def test_tutorial_video_with_camelcase_aliases(self):
        """Test TutorialVideo with camelCase field names (aliases)"""
        video = TutorialVideo(
            tutorialId="xyz-789",
            key="videos/test.mp4",
            title="Test Video",
            url="https://example.com/test.mp4",
            fileName="test.mp4",
            fileSize=2048000,
            fileType="video/mp4",
            uploadedAt="2026-01-05T10:00:00Z",
        )
        assert video.tutorial_id == "xyz-789"
        assert video.file_name == "test.mp4"
        assert video.file_size == 2048000
        assert video.file_type == "video/mp4"
        assert video.uploaded_at == "2026-01-05T10:00:00Z"

    def test_tutorial_video_populate_by_name(self):
        """Test that populate_by_name allows both snake_case and camelCase"""
        data = {
            "tutorialId": "test-123",
            "key": "test/video.mp4",
            "title": "Test",
            "url": "https://example.com/video.mp4",
            "fileName": "video.mp4",
            "fileSize": 1024,
            "fileType": "video/mp4",
        }
        video = TutorialVideo.model_validate(data)
        assert video.tutorial_id == "test-123"
        assert video.file_name == "video.mp4"

    def test_tutorial_video_model_dump_uses_aliases(self):
        """Test that model_dump uses aliases by default"""
        video = TutorialVideo(
            tutorial_id="abc-123",
            key="test.mp4",
            title="Test",
            url="https://example.com",
            file_name="test.mp4",
            file_size=1024,
            file_type="video/mp4",
        )
        data = video.model_dump(by_alias=True)
        assert "tutorialId" in data
        assert "fileName" in data
        assert "fileSize" in data
        assert "fileType" in data
        assert "uploadedAt" in data


class TestGetTutorialVideosResponse:
    """Test GetTutorialVideosResponse model"""

    def test_create_response_with_videos(self):
        """Test creating response with tutorial videos"""
        videos = [
            TutorialVideo(
                tutorial_id="abc-123",
                key="betvip/tutorials/como-apostar.mp4",
                title="Cómo Apostar",
                url="https://s3.amazonaws.com/video.mp4",
                file_name="como-apostar.mp4",
                file_size=15728640,
                file_type="video/mp4",
                uploaded_at="2026-01-05T14:30:00Z",
            ),
            TutorialVideo(
                tutorial_id="def-456",
                key="betvip/tutorials/otro-video.mp4",
                title="Otro Tutorial",
                url="https://s3.amazonaws.com/otro.mp4",
                file_name="otro-video.mp4",
                file_size=10485760,
                file_type="video/mp4",
            ),
        ]
        response = GetTutorialVideosResponse(videos=videos, count=2)
        assert len(response.videos) == 2
        assert response.count == 2
        assert response.videos[0].title == "Cómo Apostar"
        assert response.videos[1].title == "Otro Tutorial"

    def test_create_empty_response(self):
        """Test creating response with no videos"""
        response = GetTutorialVideosResponse(videos=[], count=0)
        assert len(response.videos) == 0
        assert response.count == 0

    def test_model_validate_from_dict(self):
        """Test creating response from dictionary"""
        data = {
            "videos": [
                {
                    "tutorialId": "abc-123",
                    "key": "betvip/tutorials/como-apostar.mp4",
                    "title": "Cómo Apostar",
                    "url": "https://s3.amazonaws.com/video.mp4",
                    "fileName": "como-apostar.mp4",
                    "fileSize": 15728640,
                    "fileType": "video/mp4",
                    "uploadedAt": "2026-01-05T14:30:00Z",
                }
            ],
            "count": 1,
        }
        response = GetTutorialVideosResponse.model_validate(data)
        assert response.count == 1
        assert len(response.videos) == 1
        assert response.videos[0].tutorial_id == "abc-123"


class TestUploadTutorialVideoResponse:
    """Test UploadTutorialVideoResponse model"""

    def test_create_upload_response(self):
        """Test creating upload response with all fields"""
        response = UploadTutorialVideoResponse(
            success=True,
            message="Video uploaded successfully",
            video_url="https://s3.amazonaws.com/bucket/video.mp4",
            video_key="betvip/tutorials/como-apostar.mp4",
            title="Cómo Apostar",
            tutorial_id="abc-123-uuid",
        )
        assert response.success is True
        assert response.message == "Video uploaded successfully"
        assert response.video_url == "https://s3.amazonaws.com/bucket/video.mp4"
        assert response.video_key == "betvip/tutorials/como-apostar.mp4"
        assert response.title == "Cómo Apostar"
        assert response.tutorial_id == "abc-123-uuid"

    def test_create_upload_response_with_camelcase_aliases(self):
        """Test creating upload response with camelCase field names"""
        response = UploadTutorialVideoResponse(
            success=True,
            message="Upload complete",
            videoUrl="https://example.com/video.mp4",
            videoKey="test/video.mp4",
            title="Test Video",
            tutorialId="test-123",
        )
        assert response.video_url == "https://example.com/video.mp4"
        assert response.video_key == "test/video.mp4"
        assert response.tutorial_id == "test-123"

    def test_upload_response_populate_by_name(self):
        """Test that populate_by_name allows both naming conventions"""
        data = {
            "success": True,
            "message": "Success",
            "videoUrl": "https://example.com/video.mp4",
            "videoKey": "test/video.mp4",
            "title": "Test",
            "tutorialId": "test-123",
        }
        response = UploadTutorialVideoResponse.model_validate(data)
        assert response.video_url == "https://example.com/video.mp4"
        assert response.tutorial_id == "test-123"

    def test_upload_response_failure(self):
        """Test creating upload response for failure case"""
        response = UploadTutorialVideoResponse(
            success=False,
            message="Upload failed: file too large",
            video_url="",
            video_key="",
            title="",
            tutorial_id="",
        )
        assert response.success is False
        assert "failed" in response.message.lower()

    def test_upload_response_model_dump_uses_aliases(self):
        """Test that model_dump uses aliases"""
        response = UploadTutorialVideoResponse(
            success=True,
            message="Success",
            video_url="https://example.com/video.mp4",
            video_key="test/video.mp4",
            title="Test",
            tutorial_id="test-123",
        )
        data = response.model_dump(by_alias=True)
        assert "videoUrl" in data
        assert "videoKey" in data
        assert "tutorialId" in data


class TestDeleteTutorialVideoResponse:
    """Test DeleteTutorialVideoResponse model"""

    def test_create_delete_response_with_all_fields(self):
        """Test creating delete response with all fields"""
        response = DeleteTutorialVideoResponse(
            success=True,
            message="Video deleted successfully",
            deleted_key="betvip/tutorials/como-apostar.mp4",
            deleted_tutorial_id="abc-123-uuid",
        )
        assert response.success is True
        assert response.message == "Video deleted successfully"
        assert response.deleted_key == "betvip/tutorials/como-apostar.mp4"
        assert response.deleted_tutorial_id == "abc-123-uuid"

    def test_create_delete_response_without_tutorial_id(self):
        """Test creating delete response without tutorial_id (optional field)"""
        response = DeleteTutorialVideoResponse(
            success=True,
            message="Video deleted",
            deleted_key="test/video.mp4",
        )
        assert response.success is True
        assert response.deleted_key == "test/video.mp4"
        assert response.deleted_tutorial_id is None

    def test_delete_response_with_camelcase_aliases(self):
        """Test creating delete response with camelCase field names"""
        response = DeleteTutorialVideoResponse(
            success=True,
            message="Deleted",
            deletedKey="test/video.mp4",
            deletedTutorialId="test-123",
        )
        assert response.deleted_key == "test/video.mp4"
        assert response.deleted_tutorial_id == "test-123"

    def test_delete_response_populate_by_name(self):
        """Test that populate_by_name allows both naming conventions"""
        data = {
            "success": True,
            "message": "Deleted",
            "deletedKey": "test/video.mp4",
            "deletedTutorialId": "test-123",
        }
        response = DeleteTutorialVideoResponse.model_validate(data)
        assert response.deleted_key == "test/video.mp4"
        assert response.deleted_tutorial_id == "test-123"

    def test_delete_response_failure(self):
        """Test creating delete response for failure case"""
        response = DeleteTutorialVideoResponse(
            success=False,
            message="Delete failed: video not found",
            deleted_key="",
        )
        assert response.success is False
        assert "failed" in response.message.lower()
        assert response.deleted_tutorial_id is None

    def test_delete_response_model_dump_uses_aliases(self):
        """Test that model_dump uses aliases"""
        response = DeleteTutorialVideoResponse(
            success=True,
            message="Deleted",
            deleted_key="test/video.mp4",
            deleted_tutorial_id="test-123",
        )
        data = response.model_dump(by_alias=True)
        assert "deletedKey" in data
        assert "deletedTutorialId" in data
