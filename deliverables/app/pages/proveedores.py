"""Proveedores — vendor registry backed by the database."""
import io as _io
import pandas as pd
import streamlit as st
from auth import require_auth
from file_manager import get_project_files, save_file
from i18n import t
from vendors import (
    create_vendor, delete_vendor, get_vendors, update_vendor,
    vendor_exists_from_file,
)

user = require_auth()
project_id = st.session_state.get("current_project_id")
_lang = st.session_state.get("lang", "en")

if not project_id:
    st.info(t("project.no_projects"))
    st.stop()

_is_viewer = st.session_state.get("is_viewer", False)

# ── Labels ─────────────────────────────────────────────────────────────────────
_T = {
    "title":       "Proveedores"         if _lang == "es" else "Vendors",
    "add":         "➕ Agregar proveedor" if _lang == "es" else "➕ Add vendor",
    "edit":        "✏️ Editar"            if _lang == "es" else "✏️ Edit",
    "delete":      "🗑️ Eliminar"          if _lang == "es" else "🗑️ Delete",
    "company":     "Empresa *"            if _lang == "es" else "Company *",
    "contact":     "Contacto"             if _lang == "es" else "Contact",
    "phone":       "Teléfono"             if _lang == "es" else "Phone",
    "email":       "Correo"               if _lang == "es" else "Email",
    "trade":       "Especialidad"         if _lang == "es" else "Trade / Specialty",
    "nit":         "NIT / Tax ID"         if _lang == "es" else "NIT / Tax ID",
    "status":      "Estado"               if _lang == "es" else "Status",
    "notes":       "Notas"                if _lang == "es" else "Notes",
    "save":        "💾 Guardar"           if _lang == "es" else "💾 Save",
    "cancel":      "Cancelar"             if _lang == "es" else "Cancel",
    "filters":     "Filtros"              if _lang == "es" else "Filters",
    "search":      "Buscar..."            if _lang == "es" else "Search...",
    "all":         "Todos"                if _lang == "es" else "All",
    "forms_title": "📋 Formularios de registro de proveedores"
                   if _lang == "es" else "📋 Vendor registration forms",
    "forms_help":  "Sube formularios de registro. Para cada archivo puedes registrar "
                   "al proveedor manualmente con los datos del documento."
                   if _lang == "es" else
                   "Upload registration forms. For each file you can manually register "
                   "the vendor using the information in the document.",
    "register_from_file": "➕ Registrar proveedor"
                          if _lang == "es" else "➕ Register vendor",
    "already_registered": "✅ Ya registrado" if _lang == "es" else "✅ Already registered",
    "upload_form": "📎 Subir formulario"  if _lang == "es" else "📎 Upload form",
    "no_vendors":  "No hay proveedores registrados aún."
                   if _lang == "es" else "No vendors registered yet.",
    "empty_hint":  "Agrega un proveedor manualmente o sube un formulario de registro."
                   if _lang == "es" else "Add a vendor manually or upload a registration form.",
}

STATUS_OPTS = {
    "pending":  "⏳ Pendiente" if _lang == "es" else "⏳ Pending",
    "active":   "✅ Activo"    if _lang == "es" else "✅ Active",
    "inactive": "❌ Inactivo"  if _lang == "es" else "❌ Inactive",
}

TRADE_OPTS = [
    "",
    "Arquitectura / Diseño",
    "Estructura / Concreto",
    "Mampostería y Muros",
    "Cubierta y Fachada",
    "Instalaciones Hidráulicas / Plomería",
    "Instalaciones Eléctricas",
    "HVAC / Aire Acondicionado",
    "Instalaciones Especiales (Gas, Datos, CCTV)",
    "Pisos y Revestimientos",
    "Cielos y Drywall",
    "Carpintería y Millwork",
    "Pintura y Acabados",
    "Aparatos Sanitarios y Grifería",
    "Equipos de Cocina / Restaurant",
    "Mobiliario y Decoración",
    "Señalización",
    "Preliminares y Demolición",
    "Contratista General",
    "Otro",
]


# ── Dialogs ────────────────────────────────────────────────────────────────────

@st.dialog(_T["add"])
def _add_vendor_dialog(prefill_name: str = "", source_file_id: int | None = None) -> None:
    company = st.text_input(_T["company"], value=prefill_name)
    c1, c2 = st.columns(2)
    contact = c1.text_input(_T["contact"])
    phone   = c2.text_input(_T["phone"])
    c3, c4 = st.columns(2)
    email   = c3.text_input(_T["email"])
    nit     = c4.text_input(_T["nit"])
    trade   = st.selectbox(_T["trade"], TRADE_OPTS)
    status  = st.radio(
        _T["status"],
        list(STATUS_OPTS.keys()),
        format_func=lambda k: STATUS_OPTS[k],
        horizontal=True,
        index=1,
    )
    notes = st.text_area(_T["notes"], height=70)

    bc1, bc2 = st.columns([3, 1])
    if bc1.button(_T["save"], type="primary", use_container_width=True):
        if not company.strip():
            st.error("El nombre de la empresa es obligatorio." if _lang == "es"
                     else "Company name is required.")
        else:
            create_vendor(
                project_id=project_id,
                company_name=company,
                contact_name=contact,
                phone=phone,
                email=email,
                trade=trade,
                nit=nit,
                status=status,
                notes=notes,
                source_file_id=source_file_id,
            )
            st.success("✅ Proveedor registrado." if _lang == "es" else "✅ Vendor registered.")
            st.rerun()
    if bc2.button(_T["cancel"], use_container_width=True):
        st.rerun()


@st.dialog("✏️ Editar proveedor" if _lang == "es" else "✏️ Edit vendor")
def _edit_vendor_dialog(v) -> None:
    company = st.text_input(_T["company"], value=v.company_name or "")
    c1, c2 = st.columns(2)
    contact = c1.text_input(_T["contact"], value=v.contact_name or "")
    phone   = c2.text_input(_T["phone"],   value=v.phone or "")
    c3, c4 = st.columns(2)
    email   = c3.text_input(_T["email"],  value=v.email or "")
    nit     = c4.text_input(_T["nit"],    value=v.nit or "")

    cur_trade_idx = TRADE_OPTS.index(v.trade) if v.trade in TRADE_OPTS else 0
    trade = st.selectbox(_T["trade"], TRADE_OPTS, index=cur_trade_idx)

    cur_status_idx = list(STATUS_OPTS.keys()).index(v.status) if v.status in STATUS_OPTS else 0
    status = st.radio(
        _T["status"],
        list(STATUS_OPTS.keys()),
        format_func=lambda k: STATUS_OPTS[k],
        horizontal=True,
        index=cur_status_idx,
    )
    notes = st.text_area(_T["notes"], value=v.notes or "", height=70)

    bc1, bc2 = st.columns([3, 1])
    if bc1.button(_T["save"], type="primary", use_container_width=True):
        if not company.strip():
            st.error("El nombre de la empresa es obligatorio." if _lang == "es"
                     else "Company name is required.")
        else:
            update_vendor(
                v.id,
                company_name=company,
                contact_name=contact,
                phone=phone,
                email=email,
                trade=trade,
                nit=nit,
                status=status,
                notes=notes,
            )
            st.success("✅ Actualizado." if _lang == "es" else "✅ Updated.")
            st.rerun()
    if bc2.button(_T["cancel"], use_container_width=True):
        st.rerun()


# ── Main ───────────────────────────────────────────────────────────────────────

st.title(_T["title"])
st.divider()

vendors = get_vendors(project_id)

# ── Action bar ─────────────────────────────────────────────────────────────────
if not _is_viewer:
    if st.button(_T["add"], type="primary"):
        _add_vendor_dialog()

st.divider()

# ── Vendor table ───────────────────────────────────────────────────────────────
if not vendors:
    st.info(_T["no_vendors"])
    st.caption(_T["empty_hint"])
else:
    # Build dataframe for display
    _rows = []
    for v in vendors:
        _rows.append({
            "_id":      v.id,
            "Empresa"  if _lang == "es" else "Company":   v.company_name,
            "Contacto" if _lang == "es" else "Contact":   v.contact_name or "",
            "Teléfono" if _lang == "es" else "Phone":     v.phone or "",
            "Correo"   if _lang == "es" else "Email":     v.email or "",
            "Especialidad" if _lang == "es" else "Trade": v.trade or "",
            "NIT":                                         v.nit or "",
            "Estado"   if _lang == "es" else "Status":    STATUS_OPTS.get(v.status, v.status),
        })
    df = pd.DataFrame(_rows)

    # Filters
    with st.expander(_T["filters"], expanded=False):
        fc1, fc2, fc3 = st.columns(3)
        _all = _T["all"]
        trade_opts_f = [_all] + sorted({v.trade for v in vendors if v.trade})
        status_opts_f = [_all] + [STATUS_OPTS[k] for k in STATUS_OPTS if any(v.status == k for v in vendors)]
        sel_trade  = fc1.selectbox(_T["trade"],  trade_opts_f,  key="_prov_trade")
        sel_status = fc2.selectbox(_T["status"], status_opts_f, key="_prov_status")
        keyword    = fc3.text_input(_T["search"], key="_prov_kw")

    display_df = df.drop(columns=["_id"])
    if sel_trade != _all:
        col_t = "Especialidad" if _lang == "es" else "Trade"
        display_df = display_df[display_df[col_t] == sel_trade]
    if sel_status != _all:
        col_s = "Estado" if _lang == "es" else "Status"
        display_df = display_df[display_df[col_s] == sel_status]
    if keyword:
        kw = keyword.lower()
        display_df = display_df[display_df.apply(
            lambda r: kw in " ".join(r.astype(str)).lower(), axis=1
        )]

    st.caption(f"{len(display_df)} {'proveedor(es)' if _lang == 'es' else 'vendor(s)'}")

    # Table + action buttons per row
    if not _is_viewer:
        hdr = st.columns([3, 2, 2, 2, 2, 1, 1])
        hdr[0].markdown("**Empresa**" if _lang == "es" else "**Company**")
        hdr[1].markdown("**Contacto**" if _lang == "es" else "**Contact**")
        hdr[2].markdown("**Especialidad**" if _lang == "es" else "**Trade**")
        hdr[3].markdown("**Correo**" if _lang == "es" else "**Email**")
        hdr[4].markdown("**Estado**" if _lang == "es" else "**Status**")
        hdr[5].markdown("**✏️**")
        hdr[6].markdown("**🗑️**")
        st.divider()

        for v in vendors:
            status_label = STATUS_OPTS.get(v.status, v.status)
            cols = st.columns([3, 2, 2, 2, 2, 1, 1])
            cols[0].write(v.company_name)
            cols[1].write(v.contact_name or "—")
            cols[2].write(v.trade or "—")
            cols[3].write(v.email or "—")
            cols[4].write(status_label)
            if cols[5].button("✏️", key=f"_edit_{v.id}", help=_T["edit"]):
                _edit_vendor_dialog(v)
            if cols[6].button("🗑️", key=f"_del_{v.id}", help=_T["delete"]):
                delete_vendor(v.id)
                st.rerun()
    else:
        st.dataframe(display_df, use_container_width=True, hide_index=True)

    st.divider()

    # Export
    ec1, ec2 = st.columns(2)
    _export_df = display_df.copy()
    ec1.download_button(
        "📥 CSV", _export_df.to_csv(index=False).encode("utf-8-sig"),
        file_name="proveedores.csv", mime="text/csv", use_container_width=True,
    )
    _buf = _io.BytesIO()
    with pd.ExcelWriter(_buf, engine="openpyxl") as _wr:
        _export_df.to_excel(_wr, index=False, sheet_name="Proveedores")
    ec2.download_button(
        "📥 Excel", _buf.getvalue(),
        file_name="proveedores.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )

# ── Vendor registration forms section ─────────────────────────────────────────
st.divider()
st.subheader(_T["forms_title"])
st.caption(_T["forms_help"])

if not _is_viewer:
    # Upload new registration form
    uploaded = st.file_uploader(
        _T["upload_form"],
        type=None,
        accept_multiple_files=False,
        key="_prov_uploader",
        label_visibility="collapsed",
        help="PDF, Excel, Word, imagen — cualquier formato"
             if _lang == "es" else
             "PDF, Excel, Word, image — any format",
    )
    if uploaded:
        file_bytes = uploaded.read()
        save_file(
            project_id=project_id,
            user_id=user["id"],
            filename=uploaded.name,
            file_data=file_bytes,
            content_type=uploaded.type or "application/octet-stream",
            module="proveedores",
        )
        st.success(
            f"✅ Formulario '{uploaded.name}' guardado."
            if _lang == "es" else
            f"✅ Form '{uploaded.name}' saved."
        )
        st.rerun()

# Show existing vendor-module files
prov_files = get_project_files(project_id, module="proveedores")
if not prov_files:
    st.caption(
        "Aún no hay formularios de proveedores. Sube uno arriba."
        if _lang == "es" else
        "No vendor forms yet. Upload one above."
    )
else:
    for f in prov_files:
        fc1, fc2, fc3 = st.columns([4, 2, 2])
        fc1.write(f"📄 {f.filename}")
        size_kb = round(f.file_size / 1024, 1) if f.file_size else "?"
        fc2.caption(f"{size_kb} KB · {f.uploaded_at.strftime('%Y-%m-%d') if f.uploaded_at else ''}")

        if not _is_viewer:
            already = vendor_exists_from_file(project_id, f.id)
            if already:
                fc3.success(_T["already_registered"])
            else:
                if fc3.button(_T["register_from_file"], key=f"_reg_{f.id}"):
                    _add_vendor_dialog(
                        prefill_name=f.filename.rsplit(".", 1)[0].replace("_", " ").title(),
                        source_file_id=f.id,
                    )
