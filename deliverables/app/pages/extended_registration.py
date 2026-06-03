"""Extended registration form for Vendors and Contractors."""
import streamlit as st

from auth import get_current_user
from db import ExtendedProfile, get_session
from permissions import is_pending_extended

# This page is accessible without full auth — only requires session user
_user = get_current_user()
if not _user:
    st.stop()

_lang = st.session_state.get("lang", "en")

# If user already submitted, show waiting screen
with get_session() as _s:
    _existing = _s.query(ExtendedProfile).filter_by(user_id=_user["id"]).first()

if _existing and _existing.reviewed_at is None:
    st.markdown("---")
    st.markdown(
        "<h2 style='text-align:center;color:#4fc3f7;'>&#10003;</h2>",
        unsafe_allow_html=True,
    )
    st.markdown(
        f"<p style='text-align:center;font-size:1.1rem;'>"
        f"{'Tu registro fue enviado. En breve el administrador habilitará tu acceso.' if _lang == 'es' else 'Your registration was submitted. The administrator will enable your access shortly.'}"
        f"</p>",
        unsafe_allow_html=True,
    )
    if st.button("🚪 " + ("Cerrar sesión" if _lang == "es" else "Log out")):
        from auth import logout
        logout()
    st.stop()

# ── Title ─────────────────────────────────────────────────────────────────────
st.title("Registro de Proveedor / Contratista" if _lang == "es" else "Vendor / Contractor Registration")
st.markdown(
    "Complete el formulario para finalizar tu registro. El administrador habilitará tu acceso una vez revisado."
    if _lang == "es" else
    "Complete the form to finish your registration. The administrator will enable your access after review."
)
st.divider()

CATEGORIES = [
    "Preliminares y construcción",
    "Estructura",
    "Mampostería y muros",
    "Cubierta y fachada",
    "Instalaciones hidráulicas",
    "Instalaciones eléctricas",
    "Instalaciones especiales",
    "Pisos y revestimientos",
    "Cielos y Drywall",
    "Carpintería",
    "Pintura y acabados",
    "Aparatos sanitarios",
    "Otros",
]

with st.form("extended_reg_form"):
    st.subheader("Información de la empresa" if _lang == "es" else "Company information")
    company_name = st.text_input(
        ("Nombre de la empresa *" if _lang == "es" else "Company name *"),
    )

    st.subheader("Información personal" if _lang == "es" else "Personal information")
    col1, col2, col3 = st.columns(3)
    first_name  = col1.text_input("Primer nombre *" if _lang == "es" else "First name *")
    middle_name = col2.text_input("Middle name", placeholder="Opcional / Optional")
    last_name   = col3.text_input("Primer apellido *" if _lang == "es" else "Last name *")

    col4, col5 = st.columns(2)
    phone = col4.text_input("Teléfono" if _lang == "es" else "Phone", placeholder="+57 300 000 0000")
    contact_email = col5.text_input(
        "Correo electrónico *" if _lang == "es" else "Email address *",
        value=_user["email"],
    )

    st.subheader("Categoría de trabajo" if _lang == "es" else "Work category")
    category = st.selectbox(
        "Categoría *" if _lang == "es" else "Category *",
        CATEGORIES,
    )

    submitted = st.form_submit_button(
        "📤 Enviar registro" if _lang == "es" else "📤 Submit registration",
        use_container_width=True,
        type="primary",
    )

# Handle "Otros" category — show extra field outside the form
category_other = ""
if category == "Otros":
    category_other = st.text_input(
        "Especifique la categoría *" if _lang == "es" else "Specify the category *",
        placeholder="Especifique la categoría" if _lang == "es" else "Specify the category",
        key="_cat_other",
    )

if submitted:
    errors = []
    if not company_name.strip():
        errors.append("Nombre de empresa es obligatorio." if _lang == "es" else "Company name is required.")
    if not first_name.strip():
        errors.append("Primer nombre es obligatorio." if _lang == "es" else "First name is required.")
    if not last_name.strip():
        errors.append("Primer apellido es obligatorio." if _lang == "es" else "Last name is required.")
    if not contact_email.strip() or "@" not in contact_email:
        errors.append("Correo electrónico inválido." if _lang == "es" else "Invalid email address.")
    if phone.strip() and not any(c.isdigit() for c in phone):
        errors.append("Teléfono inválido." if _lang == "es" else "Invalid phone number.")
    if category == "Otros" and not category_other.strip():
        errors.append("Especifica la categoría cuando seleccionas 'Otros'." if _lang == "es" else "Specify the category when 'Others' is selected.")

    if errors:
        for err in errors:
            st.error(err)
    else:
        final_category = category_other.strip() if category == "Otros" else category
        with get_session() as _s:
            existing_prof = _s.query(ExtendedProfile).filter_by(user_id=_user["id"]).first()
            if existing_prof:
                existing_prof.company_name  = company_name.strip()
                existing_prof.first_name    = first_name.strip()
                existing_prof.middle_name   = middle_name.strip() or None
                existing_prof.last_name     = last_name.strip()
                existing_prof.phone         = phone.strip() or None
                existing_prof.contact_email = contact_email.strip().lower()
                existing_prof.category      = final_category
            else:
                _s.add(ExtendedProfile(
                    user_id=_user["id"],
                    company_name=company_name.strip(),
                    first_name=first_name.strip(),
                    middle_name=middle_name.strip() or None,
                    last_name=last_name.strip(),
                    phone=phone.strip() or None,
                    contact_email=contact_email.strip().lower(),
                    category=final_category,
                ))
        st.success(
            "✅ Registro enviado. El administrador revisará tu información y habilitará tu acceso."
            if _lang == "es" else
            "✅ Registration submitted. The administrator will review your information and enable your access."
        )
        st.rerun()
