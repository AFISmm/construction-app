"""AI chatbot: builds project context and queries the Anthropic API."""
from __future__ import annotations

import json
from typing import Optional

import streamlit as st


def get_project_context(project_id: int) -> str:
    """Build a structured text summary of project data for the AI."""
    from db import Budget, BudgetLine, Expense, Project, User, UserPermission, get_session

    lines: list[str] = []
    with get_session() as session:
        project = session.get(Project, project_id)
        if not project:
            return "No hay datos disponibles para este proyecto."

        lines += [
            f"## Proyecto: {project.name}",
            f"Tipo: {'Residencial' if project.project_type == 'residential' else 'Comercial'}",
            f"Moneda: {project.currency}",
            "",
        ]

        # --- Financial summary ---
        budget_lines = session.query(BudgetLine).filter_by(project_id=project_id).all()
        expenses = (
            session.query(Expense)
            .filter_by(project_id=project_id)
            .order_by(Expense.expense_date.desc())
            .all()
        )
        total_budgeted = sum(float(bl.budgeted_amount) for bl in budget_lines)
        total_spent = sum(float(e.amount) for e in expenses)

        lines += [
            "## Resumen Financiero",
            f"Total presupuestado: {project.currency} {total_budgeted:,.0f}",
            f"Total ejecutado: {project.currency} {total_spent:,.0f}",
            f"Balance: {project.currency} {(total_budgeted - total_spent):,.0f}",
        ]
        if total_budgeted > 0:
            lines.append(f"Porcentaje ejecutado: {(total_spent / total_budgeted * 100):.1f}%")
        lines.append("")

        # --- Budget lines ---
        if budget_lines:
            lines.append("## Líneas de Presupuesto (primeras 20)")
            for bl in budget_lines[:20]:
                spent_line = sum(
                    float(e.amount)
                    for e in session.query(Expense).filter_by(budget_line_id=bl.id).all()
                )
                over = " ⚠️ SOBRE PRESUPUESTO" if spent_line > float(bl.budgeted_amount) > 0 else ""
                lines.append(
                    f"- {bl.description or bl.category_code}: "
                    f"Presupuesto {project.currency} {float(bl.budgeted_amount):,.0f}, "
                    f"Ejecutado {project.currency} {spent_line:,.0f}{over}"
                )
            if len(budget_lines) > 20:
                lines.append(f"... y {len(budget_lines) - 20} líneas más")
            lines.append("")

        # --- Recent expenses ---
        if expenses:
            lines.append("## Gastos/Pagos (últimos 20)")
            for e in expenses[:20]:
                lines.append(
                    f"- {e.expense_date}: {e.vendor or 'Sin proveedor'} — "
                    f"{e.description or 'Sin descripción'}: {project.currency} {float(e.amount):,.0f}"
                )
            if len(expenses) > 20:
                lines.append(f"... y {len(expenses) - 20} registros más")
            lines.append("")

            # --- Top vendors ---
            vendor_totals: dict[str, float] = {}
            for e in expenses:
                v = e.vendor or "Sin proveedor"
                vendor_totals[v] = vendor_totals.get(v, 0) + float(e.amount)
            lines.append("## Top proveedores por monto")
            for vendor, total in sorted(vendor_totals.items(), key=lambda x: -x[1])[:10]:
                lines.append(f"- {vendor}: {project.currency} {total:,.0f}")
            lines.append("")

        # --- Budget versions ---
        budgets = session.query(Budget).filter_by(project_id=project_id).all()
        if budgets:
            lines.append("## Versiones de Presupuesto")
            for b in budgets:
                lines.append(
                    f"- {b.name} v{b.version_major}.{b.version_minor} — Estado: {b.status}"
                )
            lines.append("")

        # --- Users ---
        all_perms = session.query(UserPermission).all()
        users_with_access: list[str] = []
        pending_count = 0
        for perm in all_perms:
            if perm.role == "pending":
                pending_count += 1
            elif perm.role not in ("rejected", "pending_extended"):
                proj_ids = json.loads(perm.allowed_project_ids) if perm.allowed_project_ids else None
                if proj_ids is None or project_id in proj_ids:
                    u = session.get(User, perm.user_id)
                    if u:
                        users_with_access.append(f"{u.email} ({perm.role})")

        if users_with_access:
            lines += ["## Usuarios con acceso al proyecto"] + [f"- {u}" for u in users_with_access] + [""]
        if pending_count:
            lines.append(f"## Usuarios pendientes de aprobación de cuenta: {pending_count}")

    return "\n".join(lines)


def chat_response(messages: list[dict], project_id: int) -> str:
    """Call OpenRouter (Anthropic-compatible) and return the assistant reply."""
    try:
        api_key = st.secrets.get("anthropic", {}).get("api_key", "")
        if not api_key:
            return (
                "⚠️ El chatbot no está configurado. "
                "Agrega [anthropic] api_key en los Secrets de Streamlit Cloud."
            )
        from openai import OpenAI

        context = get_project_context(project_id)
        system = (
            "Eres el Asistente IA del Portal de Construcción. "
            "Responde SIEMPRE en español con lenguaje claro y profesional. "
            "Si no tienes información suficiente para responder, indícalo explícitamente — NUNCA inventes datos. "
            "Usa listas y cifras cuando sea útil. No mezcles datos de otros proyectos.\n\n"
            f"DATOS DEL PROYECTO ACTIVO:\n{context}"
        )
        client = OpenAI(api_key=api_key, base_url="https://openrouter.ai/api/v1")
        resp = client.chat.completions.create(
            model="anthropic/claude-3-haiku",
            max_tokens=1500,
            messages=[{"role": "system", "content": system}, *messages],
        )
        return resp.choices[0].message.content
    except Exception as exc:
        return f"⚠️ Error al consultar el asistente: {exc}"


def render_chatbot(project_id: Optional[int]) -> None:
    """Render the chatbot panel at the bottom of the sidebar."""
    chat_key = f"_chat_{project_id}"
    prev_key = "_chat_prev_proj"

    # Reset history when project changes
    if st.session_state.get(prev_key) != project_id:
        for k in [k for k in st.session_state if k.startswith("_chat_")]:
            del st.session_state[k]
        st.session_state[prev_key] = project_id

    if chat_key not in st.session_state:
        st.session_state[chat_key] = []

    with st.sidebar:
        st.divider()
        with st.expander("Asistente IA", expanded=False):
            if not project_id:
                st.caption("Selecciona un proyecto para usar el asistente.")
                return

            history: list[dict] = st.session_state[chat_key]

            # Conversation display
            if not history:
                st.caption("💬 Haz una pregunta sobre el proyecto activo.")
                st.caption("Ej: ¿Cuánto se ha ejecutado del presupuesto?")
            else:
                for msg in history[-6:]:
                    if msg["role"] == "user":
                        st.markdown(
                            f'<div style="background:#1a2a3a;padding:6px 10px;border-radius:8px;'
                            f'margin:4px 0;font-size:0.85rem;">🧑 {msg["content"]}</div>',
                            unsafe_allow_html=True,
                        )
                    else:
                        st.markdown(
                            f'<div style="background:#1a3a2a;padding:6px 10px;border-radius:8px;'
                            f'margin:4px 0;font-size:0.85rem;">🤖 {msg["content"]}</div>',
                            unsafe_allow_html=True,
                        )

            # Input form
            with st.form(f"_chatform_{project_id}", clear_on_submit=True):
                user_input = st.text_area(
                    "Pregunta:",
                    placeholder="¿Cuánto se ha ejecutado del presupuesto?",
                    height=70,
                    label_visibility="collapsed",
                )
                c1, c2 = st.columns([3, 1])
                send = c1.form_submit_button("📤 Enviar", use_container_width=True, type="primary")
                clear = c2.form_submit_button("🗑️", use_container_width=True)

            if send and user_input.strip():
                history.append({"role": "user", "content": user_input.strip()})
                with st.spinner("Consultando..."):
                    reply = chat_response(history[-10:], project_id)
                history.append({"role": "assistant", "content": reply})
                st.session_state[chat_key] = history
                st.rerun()

            if clear:
                st.session_state[chat_key] = []
                st.rerun()
