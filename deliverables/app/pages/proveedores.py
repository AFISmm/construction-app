"""Proveedores — vendor directory with sample data."""
import io as _io
import pandas as pd
import streamlit as st
from auth import require_auth
from i18n import t

user = require_auth()
_lang = st.session_state.get("lang", "en")

st.title("Proveedores" if _lang == "es" else "Vendors")
st.divider()

_SAMPLE = [
    {"Empresa": "Constructora Andina S.A.S",     "Contacto": "Carlos Mendez",     "Telefono": "+57 310 234 5678", "Correo": "cmendez@andina.com",        "Categoria": "Estructura",                "Estado": "Activo"},
    {"Empresa": "Instalaciones Hydro Ltda.",      "Contacto": "Laura Rios",         "Telefono": "+57 300 876 5432", "Correo": "lrios@hydro.co",             "Categoria": "Instalaciones hidraulicas", "Estado": "Activo"},
    {"Empresa": "ElectroObra Colombia",           "Contacto": "Sergio Vargas",      "Telefono": "+57 320 111 2233", "Correo": "svargas@electroobra.com",    "Categoria": "Instalaciones electricas",  "Estado": "Activo"},
    {"Empresa": "Acabados Premium S.A.",          "Contacto": "Marcela Torres",     "Telefono": "+57 315 445 6677", "Correo": "mtorres@acabados.com",       "Categoria": "Pisos y revestimientos",    "Estado": "Activo"},
    {"Empresa": "Pinturas y Texturas Bogota",     "Contacto": "Andres Salcedo",     "Telefono": "+57 312 998 7766", "Correo": "asalcedo@pinturas.co",       "Categoria": "Pintura y acabados",        "Estado": "Activo"},
    {"Empresa": "Carpinteria Artesanal Lopez",    "Contacto": "Juan Lopez",         "Telefono": "+57 318 334 4455", "Correo": "jlopez@carpinteria.com",     "Categoria": "Carpinteria",               "Estado": "Inactivo"},
    {"Empresa": "Mamposteria del Valle",          "Contacto": "Diana Castellanos",  "Telefono": "+57 301 667 8899", "Correo": "dcastellanos@mampvalle.co",  "Categoria": "Mamposteria y muros",       "Estado": "Activo"},
    {"Empresa": "CubiertasTech S.A.S",            "Contacto": "Felipe Ruiz",        "Telefono": "+57 322 556 4433", "Correo": "fruiz@cubiertastech.com",    "Categoria": "Cubierta y fachada",        "Estado": "Activo"},
    {"Empresa": "Sanitarios y Griferia Nacional", "Contacto": "Patricia Moreno",   "Telefono": "+57 314 223 3344", "Correo": "pmoreno@sanitarios.co",      "Categoria": "Aparatos sanitarios",       "Estado": "Activo"},
    {"Empresa": "Drywall Solutions Colombia",     "Contacto": "Roberto Cano",       "Telefono": "+57 317 789 0123", "Correo": "rcano@drywallcol.com",       "Categoria": "Cielos y Drywall",          "Estado": "Activo"},
]

df_prov = pd.DataFrame(_SAMPLE)

with st.expander("Filtros" if _lang == "es" else "Filters", expanded=False):
    fc1, fc2, fc3 = st.columns(3)
    _all = "Todos" if _lang == "es" else "All"
    cats    = [_all] + sorted(df_prov["Categoria"].unique().tolist())
    estados = [_all] + sorted(df_prov["Estado"].unique().tolist())
    sel_cat    = fc1.selectbox("Categoria" if _lang == "es" else "Category", cats)
    sel_estado = fc2.selectbox("Estado"    if _lang == "es" else "Status",   estados)
    keyword    = fc3.text_input("Buscar..." if _lang == "es" else "Search...", key="_prov_kw")

filtered_df = df_prov.copy()
if sel_cat    != _all: filtered_df = filtered_df[filtered_df["Categoria"] == sel_cat]
if sel_estado != _all: filtered_df = filtered_df[filtered_df["Estado"]    == sel_estado]
if keyword:
    kw = keyword.lower()
    filtered_df = filtered_df[filtered_df.apply(lambda r: kw in " ".join(r.astype(str)).lower(), axis=1)]

st.caption(f"{len(filtered_df)} {'proveedor(es)' if _lang == 'es' else 'vendor(s)'}")
st.dataframe(filtered_df, use_container_width=True, hide_index=True)

st.divider()
ec1, ec2 = st.columns(2)
ec1.download_button(
    "📥 CSV", filtered_df.to_csv(index=False).encode("utf-8-sig"),
    file_name="proveedores.csv", mime="text/csv", use_container_width=True,
)
_buf = _io.BytesIO()
with pd.ExcelWriter(_buf, engine="openpyxl") as _wr:
    filtered_df.to_excel(_wr, index=False, sheet_name="Proveedores")
ec2.download_button(
    "📥 Excel", _buf.getvalue(),
    file_name="proveedores.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    use_container_width=True,
)
