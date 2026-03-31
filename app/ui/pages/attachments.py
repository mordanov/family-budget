"""Attachments page — upload and manage file attachments per operation."""
import streamlit as st

from app.db.connection import run_async
from app.services.attachment_service import AttachmentService
from app.services.operation_service import OperationService
from app.ui.components.tables import attachments_table
from app.utils.validators import ValidationError
from app.utils.formatters import format_file_size
from app.config import settings


MIME_MAP = {
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "png": "image/png",
    "gif": "image/gif",
    "webp": "image/webp",
    "pdf": "application/pdf",
}


def _guess_mime(filename: str) -> str:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return MIME_MAP.get(ext, "application/octet-stream")


def render():
    st.title("Attachments")

    att_svc = AttachmentService()
    op_svc = OperationService()

    tab_browse, tab_upload, tab_delete = st.tabs(["Browse", "Upload", "Delete"])

    # ── BROWSE ────────────────────────────────────────────────────────────────
    with tab_browse:
        st.subheader("Attachments for an Operation")
        op_id = st.number_input("Operation ID", min_value=1, step=1, key="browse_op_id")

        if st.button("Load Attachments", key="browse_load"):
            try:
                atts = run_async(att_svc.get_by_operation(int(op_id)))
                st.session_state["browse_atts"] = atts
            except Exception as e:
                st.error(f"Error: {e}")

        if "browse_atts" in st.session_state:
            atts = st.session_state["browse_atts"]
            if not atts:
                st.info("No attachments for this operation.")
            else:
                attachments_table(atts)
                st.markdown("---")
                st.subheader("Preview")
                for att in atts:
                    with st.expander(f"{att.file_name} ({format_file_size(att.file_size)})"):
                        file_bytes = att_svc.read_file(att)
                        if file_bytes is None:
                            st.warning("File not found on disk.")
                        elif att.is_image:
                            st.image(file_bytes, caption=att.file_name)
                        elif att.is_pdf:
                            st.download_button(
                                label="Download PDF",
                                data=file_bytes,
                                file_name=att.file_name,
                                mime="application/pdf",
                            )
                        else:
                            st.download_button(
                                label="Download File",
                                data=file_bytes,
                                file_name=att.file_name,
                            )

    # ── UPLOAD ────────────────────────────────────────────────────────────────
    with tab_upload:
        st.subheader("Upload Attachment")
        st.caption(
            f"Allowed: images (JPEG, PNG, GIF, WebP) and PDF. "
            f"Max size: {settings.MAX_FILE_SIZE_MB} MB"
        )

        with st.form("upload_form", clear_on_submit=True):
            upload_op_id = st.number_input("Operation ID *", min_value=1, step=1, key="up_op_id")
            uploaded_file = st.file_uploader(
                "Choose file",
                type=["jpg", "jpeg", "png", "gif", "webp", "pdf"],
            )
            submitted = st.form_submit_button("Upload", type="primary")

        if submitted:
            if not uploaded_file:
                st.error("Please select a file.")
            else:
                try:
                    file_bytes = uploaded_file.read()
                    mime_type = _guess_mime(uploaded_file.name)
                    att = run_async(att_svc.upload(
                        operation_id=int(upload_op_id),
                        file_name=uploaded_file.name,
                        file_bytes=file_bytes,
                        mime_type=mime_type,
                    ))
                    st.success(
                        f"Uploaded '{att.file_name}' ({format_file_size(att.file_size)}). "
                        f"Attachment ID: {att.id}"
                    )
                except ValidationError as e:
                    st.error(f"{e.field}: {e.message}")
                except Exception as e:
                    st.error(f"Upload failed: {e}")

    # ── DELETE ────────────────────────────────────────────────────────────────
    with tab_delete:
        st.subheader("Delete Attachment")
        att_id = st.number_input("Attachment ID", min_value=1, step=1, key="del_att_id")

        if st.button("Delete Attachment", type="secondary"):
            try:
                run_async(att_svc.delete(int(att_id)))
                st.success(f"Attachment #{att_id} deleted.")
            except ValidationError as e:
                st.error(e.message)
            except Exception as e:
                st.error(f"Error: {e}")
