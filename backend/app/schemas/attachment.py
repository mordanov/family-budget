from datetime import datetime
from pydantic import BaseModel


class AttachmentResponse(BaseModel):
    id: int
    filename: str
    original_filename: str
    file_path: str
    mime_type: str
    file_size: int
    description: str | None
    operation_id: int
    public_url: str
    created_at: datetime

    model_config = {"from_attributes": True}
