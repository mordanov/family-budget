"""Operations CRUD page."""
import streamlit as st
from datetime import datetime, date
from decimal import Decimal
from typing import Optional

from app.db.connection import run_async
from app.services.operation_service import OperationService
from app.services.category_service import CategoryService
from app.services.user_service import UserService
from app.models.operation import OperationFilter
from app.models.enums import OperationType, PaymentType, Currency
from app.ui.components.forms import (
    operation_type_selector, payment_type_selector, currency_selector,
    amount_input, date_input, category_selector, user_selector,
    description_input, recurring_inputs, date_range_selector,
)
from app.ui.components.tables import operations_table
from app.utils.validators import ValidationError
from app.utils.formatters import format_month_year


def render():
    st.title("Operations")

    op_svc = OperationService()
    cat_svc = CategoryService()
    user_svc = UserService()

    try:
        categories = run_async(cat_svc.get_all())
        users = run_async(user_svc.get_all())
    except Exception as e:
        st.error(f"Failed to load reference data: {e}")
        return

    # Tabs
    tab_list, tab_add, tab_edit = st.tabs(["List", "Add New", "Edit / Delete"])

    # ── LIST ──────────────────────────────────────────────────────────────────
    with tab_list:
        st.subheader("Filter Operations")
        now = datetime.now()
        date_from, date_to = date_range_selector("ops_filter", now.year, now.month)

        col1, col2, col3 = st.columns(3)
        with col1:
            filter_type = st.selectbox(
                "Type", ["All", "Expense", "Income"], key="fl_type"
            )
        with col2:
            filter_cat = st.selectbox(
                "Category",
                ["All"] + [c.name for c in categories],
                key="fl_cat",
            )
        with col3:
            filter_user = st.selectbox(
                "User",
                ["All"] + [u.name for u in users],
                key="fl_user",
            )

        search = st.text_input("Search description", key="fl_search")

        f = OperationFilter(date_from=date_from, date_to=date_to)
        if filter_type != "All":
            f.operation_type = OperationType(filter_type.lower())
        if filter_cat != "All":
            cat = next((c for c in categories if c.name == filter_cat), None)
            if cat:
                f.category_id = cat.id
        if filter_user != "All":
            user = next((u for u in users if u.name == filter_user), None)
            if user:
                f.user_id = user.id
        if search:
            f.search = search

        try:
            ops, total = run_async(op_svc.get_many(f, limit=200))
        except Exception as e:
            st.error(f"Error: {e}")
            ops, total = [], 0

        st.caption(f"Found {total} operation(s)")
        operations_table(ops)

    # ── ADD NEW ───────────────────────────────────────────────────────────────
    with tab_add:
        st.subheader("Add New Operation")

        with st.form("add_op_form", clear_on_submit=True):
            op_type = operation_type_selector("add_op_type")
            pay_type = payment_type_selector(op_type, "add_pay_type")
            amount = amount_input("add_amount")
            currency = currency_selector("add_currency")
            cat_id = category_selector(categories, "add_cat")
            user_id = user_selector(users, "add_user")
            op_date = date_input("Date", "add_date")
            desc = description_input("add_desc")
            is_recurring, forecast_end = recurring_inputs("add_rec")

            submitted = st.form_submit_button("Save Operation", type="primary")

        if submitted:
            if not amount:
                st.error("Amount is required.")
            elif not op_date:
                st.error("Date is required.")
            elif not cat_id:
                st.error("Category is required.")
            elif not user_id:
                st.error("User is required.")
            else:
                try:
                    op = run_async(op_svc.create(
                        amount=amount,
                        currency=currency,
                        operation_type=op_type,
                        payment_type=pay_type,
                        category_id=cat_id,
                        user_id=user_id,
                        operation_date=op_date,
                        description=desc,
                        is_recurring=is_recurring,
                        forecast_end_date=forecast_end,
                    ))
                    st.success(f"Operation #{op.id} created successfully!")
                except ValidationError as e:
                    st.error(f"Validation error — {e.field}: {e.message}")
                except Exception as e:
                    st.error(f"Error: {e}")

    # ── EDIT / DELETE ─────────────────────────────────────────────────────────
    with tab_edit:
        st.subheader("Edit or Delete Operation")
        op_id_input = st.number_input("Operation ID", min_value=1, step=1, key="edit_op_id")

        if st.button("Load Operation"):
            try:
                op = run_async(op_svc.get_by_id(int(op_id_input)))
                st.session_state["edit_op"] = op
            except ValidationError as e:
                st.error(e.message)
            except Exception as e:
                st.error(f"Error: {e}")

        if "edit_op" in st.session_state:
            op = st.session_state["edit_op"]
            st.write(f"Editing operation #{op.id} — **{op.operation_type.value}** {float(op.amount):,.2f}")

            with st.form("edit_op_form"):
                new_type = operation_type_selector("ed_op_type")
                new_pay = payment_type_selector(new_type, "ed_pay_type",
                                                default=op.payment_type)
                new_amount = amount_input("ed_amount", default=float(op.amount))
                new_currency = currency_selector("ed_currency", default=op.currency.value)
                new_cat = category_selector(categories, "ed_cat", default_id=op.category_id)
                new_user = user_selector(users, "ed_user", default_id=op.user_id)
                new_date = date_input("Date", "ed_date",
                                     default=op.operation_date.date() if op.operation_date else None)
                new_desc = description_input("ed_desc", default=op.description or "")
                new_recurring, new_end = recurring_inputs("ed_rec")

                col_save, col_del = st.columns(2)
                with col_save:
                    save_btn = st.form_submit_button("Update", type="primary")
                with col_del:
                    del_btn = st.form_submit_button("Delete", type="secondary")

            if save_btn:
                try:
                    updated = run_async(op_svc.update(
                        op.id,
                        amount=new_amount,
                        currency=new_currency,
                        operation_type=new_type,
                        payment_type=new_pay,
                        category_id=new_cat,
                        user_id=new_user,
                        operation_date=new_date,
                        description=new_desc,
                        is_recurring=new_recurring,
                        forecast_end_date=new_end,
                    ))
                    st.success(f"Operation #{op.id} updated!")
                    del st.session_state["edit_op"]
                    st.rerun()
                except ValidationError as e:
                    st.error(f"{e.field}: {e.message}")
                except Exception as e:
                    st.error(f"Error: {e}")

            if del_btn:
                try:
                    run_async(op_svc.delete(op.id))
                    st.success(f"Operation #{op.id} deleted.")
                    del st.session_state["edit_op"]
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")
