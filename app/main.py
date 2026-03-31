"""
Family Budget — Streamlit Application Entry Point
"""
import streamlit as st
import asyncio

from app.config import settings
from app.utils.logger import get_logger

logger = get_logger("main")


def configure_page():
    st.set_page_config(
        page_title=settings.APP_NAME,
        page_icon="💰",
        layout="wide",
        initial_sidebar_state="expanded",
    )


def sidebar_navigation() -> str:
    with st.sidebar:
        st.title("💰 Family Budget")
        st.markdown("---")

        pages = {
            "dashboard": "🏠 Dashboard",
            "operations": "📋 Operations",
            "reports": "📊 Reports",
            "categories": "🏷️ Categories",
            "attachments": "📎 Attachments",
        }

        if "page" not in st.session_state:
            st.session_state["page"] = "dashboard"

        for key, label in pages.items():
            active = st.session_state.get("page") == key
            btn_type = "primary" if active else "secondary"
            if st.button(label, key=f"nav_{key}", use_container_width=True, type=btn_type):
                st.session_state["page"] = key

        st.markdown("---")
        st.caption(f"v1.0.0 | {settings.APP_NAME}")

        # DB health indicator
        if st.button("Check DB", key="health_btn"):
            from app.db.connection import health_check, run_async
            healthy = run_async(health_check())
            if healthy:
                st.success("Database OK")
            else:
                st.error("Database unreachable")

    return st.session_state.get("page", "dashboard")


def main():
    configure_page()

    # Apply nest_asyncio for Streamlit + asyncpg compatibility
    try:
        import nest_asyncio
        nest_asyncio.apply()
    except ImportError:
        pass

    current_page = sidebar_navigation()

    # Route to page
    try:
        if current_page == "dashboard":
            from app.ui.pages.dashboard import render
        elif current_page == "operations":
            from app.ui.pages.operations import render
        elif current_page == "reports":
            from app.ui.pages.reports import render
        elif current_page == "categories":
            from app.ui.pages.categories import render
        elif current_page == "attachments":
            from app.ui.pages.attachments import render
        else:
            from app.ui.pages.dashboard import render

        render()
    except Exception as e:
        logger.exception(f"Unhandled error on page '{current_page}': {e}")
        st.error(f"An unexpected error occurred: {e}")
        st.info("Check logs for details.")


if __name__ == "__main__":
    main()
