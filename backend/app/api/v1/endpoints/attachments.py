from fastapi import APIRouter, Depends, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.attachment import AttachmentResponse
from app.services.attachment_service import AttachmentService

router = APIRouter(prefix="/attachments", tags=["attachments"])


@router.get("/operation/{operation_id}", response_model=list[AttachmentResponse])
async def list_attachments(
    operation_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return await AttachmentService(db).get_by_operation(operation_id)


@router.post("/operation/{operation_id}", response_model=AttachmentResponse, status_code=201)
async def upload_attachment(
    operation_id: int,
    file: UploadFile = File(...),
    description: str | None = Form(None),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return await AttachmentService(db).upload(operation_id, file, description)


@router.delete("/{attachment_id}", status_code=204)
async def delete_attachment(
    attachment_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    await AttachmentService(db).delete(attachment_id)
