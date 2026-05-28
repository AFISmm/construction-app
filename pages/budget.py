"""Budget Setup page — CRUD for budget lines per category."""
import streamlit as st
from app.auth import require_auth
from app.budget import create_budget_line, delete_budget_line, get_all_categories, get_budget_lines, get_line_spent
from app.db import Room, get_session
from app.i18n import t

user = require_auth()
project_id = st.session_state.get("current_project_id")
if not project_id:
    st.info(t("project.no_projects"))
    st.stop()

st.title(t("budget.title"))

# ---------- Add line form ----------
with st.expander(t("budget.add_line")):
    with st.form("add_budget_line"):
        categories = get_all_categories()
        cat_options = {f"{c.code} — {c.name}": c.code for c in categories}
        with get_session() as s:
            rooms = s.query(Room).filter_by(project_id=project_id).all()
        room_options = {t("budget.room_all"): None} | {r.name: r.id for r in rooms}

        selected_cat = st.selectbox(t("budget.category_label") + " *", list(cat_options.keys()))
        selected_room = st.selectbox(t("budget.room_label"), list(room_options.keys()))
        description = st.text_input(t("budget.description_label"))
        amount = st.number_input(t("budget.amount_label") + " *", min_value=0.0, step=1000.0)
        if st.form_submit_button(t("common.save")):
            if amount <= 0:
                st.error(t("error.invalid_amount"))
            else:
                create_budget_line(project_id, cat_options[selected_cat], amount,
                                   description, room_options[selected_room])
                st.success(t("budget.line_saved"))
                st.rerun()

# ---------- Lines table ----------
lines = get_budget_lines(project_id)
with get_session() as _s:
    _rooms = _s.query(Room).filter_by(project_id=project_id).all()
    room_name_map: dict[int, str] = {r.id: r.name for r in _rooms}

if not lines:
    st.info(t("budget.no_lines"))
else:
    # Group by top-level category
    groups: dict[str, list] = {}
    for line in lines:
        top = line.category_code.split(".")[0]
        groups.setdefault(top, []).append(line)

    # Build top-level category name map (level == 1 entries have no dot in code)
    top_cat_names: dict[str, str] = {
        c.code: c.name for c in get_all_categories() if c.level == 1
    }

    for top_code, group_lines in sorted(groups.items()):
        cat_label = top_cat_names.get(top_code, top_code)
        st.subheader(f"{top_code} — {cat_label}")
        for line in group_lines:
            spent = get_line_spent(line.id)
            col_cat, col_desc, col_room, col_bud, col_spent, col_del = st.columns([2, 2, 1, 1, 1, 0.5])
            col_cat.write(line.category_code)
            col_desc.write(line.description or "—")
            col_room.write(room_name_map.get(line.room_id, "—") if line.room_id else "—")
            col_bud.write(f"{line.budgeted_amount:,.0f}")
            col_spent.write(f":red[{spent:,.0f}]" if spent > float(line.budgeted_amount) else f"{spent:,.0f}")
            if col_del.button("x", key=f"del_line_{line.id}"):
                delete_budget_line(line.id, project_id)
                st.rerun()
        if any(float(l.budgeted_amount) < get_line_spent(l.id) for l in group_lines):
            st.warning(t("budget.over_budget_warning"))
