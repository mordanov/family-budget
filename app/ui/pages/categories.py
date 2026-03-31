"""Categories CRUD page."""
import streamlit as st

from app.db.connection import run_async
from app.services.category_service import CategoryService
from app.ui.components.tables import categories_table
from app.utils.validators import ValidationError


PRESET_COLORS = ["#e74c3c", "#3498db", "#2ecc71", "#f39c12", "#9b59b6",
                 "#1abc9c", "#e67e22", "#34495e", "#e91e63", "#808080"]

PRESET_ICONS = ["🏠", "🚗", "🍔", "💊", "📚", "🎮", "✈️", "👗",
                "💡", "📱", "🎵", "🏋️", "💰", "🛒", "📁"]


def render():
    st.title("Categories")
    svc = CategoryService()

    try:
        categories = run_async(svc.get_all())
    except Exception as e:
        st.error(f"Failed to load categories: {e}")
        return

    tab_list, tab_add, tab_edit = st.tabs(["List", "Add New", "Edit / Delete"])

    # ── LIST ──────────────────────────────────────────────────────────────────
    with tab_list:
        st.subheader(f"All Categories ({len(categories)})")
        categories_table(categories)

    # ── ADD ───────────────────────────────────────────────────────────────────
    with tab_add:
        st.subheader("Add Category")

        with st.form("add_cat_form", clear_on_submit=True):
            name = st.text_input("Name *", max_chars=100)
            description = st.text_area("Description", max_chars=500)
            col1, col2 = st.columns(2)
            with col1:
                icon = st.selectbox("Icon", PRESET_ICONS, key="add_icon")
            with col2:
                color = st.selectbox("Color", PRESET_COLORS, key="add_color")
            submitted = st.form_submit_button("Create", type="primary")

        if submitted:
            if not name.strip():
                st.error("Name is required.")
            else:
                try:
                    cat = run_async(svc.create(
                        name=name.strip(),
                        description=description.strip() or None,
                        color=color,
                        icon=icon,
                    ))
                    st.success(f"Category '{cat.name}' created!")
                    st.rerun()
                except ValidationError as e:
                    st.error(f"{e.field}: {e.message}")
                except Exception as e:
                    st.error(f"Error: {e}")

    # ── EDIT ──────────────────────────────────────────────────────────────────
    with tab_edit:
        st.subheader("Edit or Delete Category")

        if not categories:
            st.info("No categories to edit.")
            return

        cat_names = [f"[{c.id}] {c.icon or ''} {c.name}" for c in categories]
        selected_label = st.selectbox("Select category", cat_names, key="sel_cat_edit")
        selected_id = int(selected_label.split("]")[0][1:])
        selected = next(c for c in categories if c.id == selected_id)

        with st.form("edit_cat_form"):
            new_name = st.text_input("Name", value=selected.name)
            new_desc = st.text_area("Description", value=selected.description or "")
            col1, col2 = st.columns(2)
            with col1:
                new_icon_idx = PRESET_ICONS.index(selected.icon) if selected.icon in PRESET_ICONS else 0
                new_icon = st.selectbox("Icon", PRESET_ICONS, index=new_icon_idx, key="ed_icon")
            with col2:
                new_color_idx = PRESET_COLORS.index(selected.color) if selected.color in PRESET_COLORS else 0
                new_color = st.selectbox("Color", PRESET_COLORS, index=new_color_idx, key="ed_color")

            col_save, col_del = st.columns(2)
            with col_save:
                save_btn = st.form_submit_button("Update", type="primary")
            with col_del:
                del_btn = st.form_submit_button("Delete", type="secondary")

        if save_btn:
            try:
                run_async(svc.update(
                    selected.id,
                    name=new_name.strip() or None,
                    description=new_desc.strip() or None,
                    color=new_color,
                    icon=new_icon,
                ))
                st.success("Category updated!")
                st.rerun()
            except ValidationError as e:
                st.error(f"{e.field}: {e.message}")
            except Exception as e:
                st.error(f"Error: {e}")

        if del_btn:
            try:
                run_async(svc.delete(selected.id))
                st.success(f"Category '{selected.name}' deleted.")
                st.rerun()
            except ValidationError as e:
                st.error(e.message)
            except Exception as e:
                st.error(f"Error: {e}")
