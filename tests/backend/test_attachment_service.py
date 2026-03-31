"""Tests for AttachmentService (mock-based, with tmp_path for file I/O)."""
import os
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, patch, MagicMock

from app.services.attachment_service import AttachmentService
from app.models.attachment import Attachment
from app.utils.validators import ValidationError


def _make_attachment(id=1, operation_id=5, file_path="/tmp/test/5/abc.png"):
    return Attachment(
        id=id,
        operation_id=operation_id,
        file_name="receipt.png",
        file_path=file_path,
        mime_type="image/png",
        file_size=1024,
        upload_date=datetime.now(),
        created_at=datetime.now(),
    )


@pytest.mark.asyncio
class TestAttachmentService:
    def _make_svc(self):
        svc = AttachmentService()
        svc.repo = AsyncMock()
        return svc

    async def test_get_by_operation(self):
        svc = self._make_svc()
        svc.repo.get_by_operation.return_value = [_make_attachment()]

        result = await svc.get_by_operation(5)

        assert len(result) == 1
        svc.repo.get_by_operation.assert_awaited_once_with(5)

    async def test_get_by_id_found(self):
        svc = self._make_svc()
        att = _make_attachment()
        svc.repo.get_by_id.return_value = att

        result = await svc.get_by_id(1)

        assert result.id == 1

    async def test_get_by_id_not_found(self):
        svc = self._make_svc()
        svc.repo.get_by_id.return_value = None

        with pytest.raises(ValidationError) as exc:
            await svc.get_by_id(99)
        assert exc.value.field == "id"

    async def test_upload_success(self, tmp_path):
        svc = self._make_svc()
        file_bytes = b"PNG_DATA"
        expected_path = str(tmp_path / "5" / "somefile.png")
        att = _make_attachment(file_path=expected_path)
        svc.repo.create.return_value = att

        with patch("app.services.attachment_service.settings") as mock_settings:
            mock_settings.upload_dir_path = str(tmp_path)
            mock_settings.max_file_size_bytes = 10 * 1024 * 1024
            mock_settings.allowed_mime_types_list = ["image/png", "image/jpeg", "application/pdf"]
            result = await svc.upload(
                operation_id=5,
                file_name="receipt.png",
                file_bytes=file_bytes,
                mime_type="image/png",
            )

        assert result.id == 1
        svc.repo.create.assert_awaited_once()

    async def test_upload_file_too_large(self, tmp_path):
        svc = self._make_svc()

        with patch("app.services.attachment_service.settings") as mock_settings:
            mock_settings.upload_dir_path = str(tmp_path)
            mock_settings.max_file_size_bytes = 10  # 10 bytes max
            mock_settings.allowed_mime_types_list = ["image/png"]

            with pytest.raises(ValidationError):
                await svc.upload(
                    operation_id=5,
                    file_name="big.png",
                    file_bytes=b"x" * 100,
                    mime_type="image/png",
                )
        svc.repo.create.assert_not_awaited()

    async def test_upload_invalid_mime(self, tmp_path):
        svc = self._make_svc()

        with patch("app.services.attachment_service.settings") as mock_settings:
            mock_settings.upload_dir_path = str(tmp_path)
            mock_settings.max_file_size_bytes = 10 * 1024 * 1024
            mock_settings.allowed_mime_types_list = ["image/png"]

            with pytest.raises(ValidationError):
                await svc.upload(
                    operation_id=5,
                    file_name="virus.exe",
                    file_bytes=b"data",
                    mime_type="application/exe",
                )
        svc.repo.create.assert_not_awaited()

    async def test_delete_success_removes_file(self, tmp_path):
        svc = self._make_svc()
        # Create a real file so os.remove works
        file_path = tmp_path / "receipt.png"
        file_path.write_bytes(b"data")
        att = _make_attachment(file_path=str(file_path))
        svc.repo.get_by_id.return_value = att
        svc.repo.delete.return_value = True

        result = await svc.delete(1)

        assert result is True
        assert not file_path.exists()

    async def test_delete_success_missing_file(self, tmp_path):
        svc = self._make_svc()
        att = _make_attachment(file_path=str(tmp_path / "gone.png"))
        svc.repo.get_by_id.return_value = att
        svc.repo.delete.return_value = True

        # Should not raise even if file is already gone
        result = await svc.delete(1)

        assert result is True

    async def test_delete_not_found(self):
        svc = self._make_svc()
        svc.repo.get_by_id.return_value = None

        with pytest.raises(ValidationError) as exc:
            await svc.delete(99)
        assert exc.value.field == "id"
        svc.repo.delete.assert_not_awaited()

    def test_read_file_success(self, tmp_path):
        svc = AttachmentService()
        svc.repo = AsyncMock()
        file_path = tmp_path / "data.png"
        file_path.write_bytes(b"image_data")
        att = _make_attachment(file_path=str(file_path))

        content = svc.read_file(att)

        assert content == b"image_data"

    def test_read_file_not_found(self, tmp_path):
        svc = AttachmentService()
        svc.repo = AsyncMock()
        att = _make_attachment(file_path=str(tmp_path / "missing.png"))

        content = svc.read_file(att)

        assert content is None

    def test_generate_path_creates_directory(self, tmp_path):
        svc = AttachmentService()
        svc.repo = AsyncMock()

        with patch("app.services.attachment_service.settings") as mock_settings:
            mock_settings.upload_dir_path = str(tmp_path)
            path = svc._generate_path(operation_id=42, original_name="photo.jpg")

        assert str(tmp_path / "42") in path
        assert path.endswith(".jpg")
        assert os.path.isdir(str(tmp_path / "42"))

    def test_generate_path_preserves_extension(self, tmp_path):
        svc = AttachmentService()
        svc.repo = AsyncMock()

        with patch("app.services.attachment_service.settings") as mock_settings:
            mock_settings.upload_dir_path = str(tmp_path)
            path = svc._generate_path(operation_id=1, original_name="doc.PDF")

        assert path.endswith(".pdf")
