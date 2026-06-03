# Guia de Despliegue — Construction Budget Control

**Plataforma:** Streamlit Community Cloud + Supabase (PostgreSQL)
**Repositorio:** `https://github.com/AFISmm/construction-app.git`
**Archivo principal:** `main.py`
**Tiempo estimado total:** 20–30 minutos

> Esta guia asume que ya tienes cuentas activas en GitHub (`AFISmm`) y en Streamlit Community Cloud. No cubre la creacion de esas cuentas.

---

## Bloque 1 — Crear la base de datos en Supabase (5–10 min)

### 1.1 Crear el proyecto en Supabase

1. Ve a [https://supabase.com](https://supabase.com) e inicia sesion (crea la cuenta gratis si aun no la tienes).
2. En el dashboard, haz clic en **"New project"**.
3. Elige una organizacion (o crea una nueva), pon un nombre al proyecto — por ejemplo `construction-app` — y elige la region mas cercana a ti.
4. En el campo **"Database Password"**, crea una contrasena segura y **guardala en un lugar seguro ahora** — la necesitaras en los bloques siguientes y Supabase no te la vuelve a mostrar completa.
5. Haz clic en **"Create new project"** y espera aproximadamente 2 minutos mientras Supabase aprovisiona la base de datos. La pantalla te mostrara una barra de progreso.

### 1.2 Obtener la URI de conexion

Una vez que el proyecto este listo:

1. Ve a **Project Settings** (icono de engranaje en la barra lateral izquierda).
2. Selecciona la seccion **Database**.
3. Desplazate hasta **"Connection string"** y asegurate de que el modo sea **"URI"**.
4. Copia la URI. Tendra este formato:

   ```
   postgresql://postgres:[YOUR-PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres
   ```

5. Reemplaza `[YOUR-PASSWORD]` con la contrasena que guardaste en el paso 1.1.

> **Nota sobre caracteres especiales en la contrasena:** Si tu contrasena contiene caracteres como `@`, `#`, `$`, `%`, `&`, `+`, `=`, `/`, `?`, o espacios, debes codificarlos en URL antes de insertarlos en la URI. Por ejemplo:
> - `@` se convierte en `%40`
> - `#` se convierte en `%23`
> - `$` se convierte en `%24`
>
> Puedes usar [https://www.urlencoder.org](https://www.urlencoder.org) para codificar solo la contrasena (no toda la URI).

---

## Bloque 2 — Configurar email para OTP (Gmail App Password)

La app envia codigos de un solo uso (OTP) por correo electronico para autenticar a los usuarios. Necesitas una cuenta Gmail con autenticacion de dos factores activada.

### 2.1 Activar verificacion en 2 pasos

1. Ve a [https://myaccount.google.com](https://myaccount.google.com) con la cuenta Gmail que usaras.
2. En el menu lateral, haz clic en **"Seguridad"** (o **"Security"** si esta en ingles).
3. Busca la seccion **"Como accedes a Google"** y activa **"Verificacion en 2 pasos"** si no esta activada. Sigue los pasos que Google te indica.

### 2.2 Crear la contrasena de aplicacion

1. Una vez activada la verificacion en 2 pasos, vuelve a **Seguridad** en tu cuenta de Google.
2. Busca **"Contrasenas de aplicaciones"** (puede aparecer en la seccion "Como accedes a Google" o en el buscador de la pagina).
3. En el campo de nombre, escribe `ConstructionApp` y haz clic en **"Crear"**.
4. Google te mostrara una contrasena de **16 caracteres** (sin espacios). Copiala y guardala — solo se muestra una vez.

### 2.3 Valores SMTP que usaras en los secrets

| Campo | Valor |
|---|---|
| `smtp_host` | `smtp.gmail.com` |
| `smtp_port` | `587` |
| `smtp_user` | Tu direccion de Gmail completa (ej: `tuusuario@gmail.com`) |
| `smtp_password` | La contrasena de aplicacion de 16 caracteres |
| `from_address` | La misma direccion de Gmail |

---

## Bloque 3 — Crear repositorio en GitHub y hacer el primer push

### 3.1 Crear el repositorio en GitHub

1. Ve a [https://github.com/new](https://github.com/new) con tu cuenta `AFISmm`.
2. Nombre del repositorio: `construction-app`.
3. Visibilidad: **Private** (recomendado — el codigo contiene logica de negocio).
4. **No marques ninguna casilla** de inicializacion (sin README, sin .gitignore, sin licencia) — el repositorio debe quedar completamente vacio.
5. Haz clic en **"Create repository"**.

### 3.2 Hacer el primer push

Abre una terminal (Command Prompt, PowerShell, o Git Bash) y navega a la carpeta `deliverables/app/` dentro de tu proyecto local. Luego ejecuta estos comandos en orden:

```bash
git init
git add .
git commit -m "Initial commit — ConstructionApp"
git branch -M main
git remote add origin https://github.com/AFISmm/construction-app.git
git push -u origin main
```

Si GitHub te pide autenticacion, ingresa tu usuario `AFISmm` y un Personal Access Token (no tu contrasena — GitHub ya no acepta contrasenas para operaciones Git. Si no tienes un token, crealo en [https://github.com/settings/tokens](https://github.com/settings/tokens) con permiso `repo`).

### 3.3 Verificar que los secrets NO se subieron

Una vez que el push termine, abre el repositorio en GitHub (`https://github.com/AFISmm/construction-app`) y confirma lo siguiente:

- **No debe aparecer** ningun archivo `secrets.toml` en ninguna carpeta.
- **No debe aparecer** ningun archivo `.db`, `.sqlite` o `.sqlite3`.
- **Si aparecen**, detente: significa que el `.gitignore` no funciono correctamente. Borra esos archivos del repo y revisa que el `.gitignore` en `deliverables/app/` tenga las reglas correctas.

---

## Bloque 4 — Publicar en Streamlit Community Cloud

### 4.1 Crear la nueva app

1. Ve a [https://share.streamlit.io](https://share.streamlit.io) e inicia sesion con tu cuenta de GitHub.
2. Haz clic en **"New app"**.
3. Selecciona el repositorio: `AFISmm/construction-app`.
4. Branch: `main`.
5. Main file path: `main.py`

   > Este es el nombre exacto del archivo de entrada de la app, confirmado en el README del proyecto.

### 4.2 Configurar los secrets en Streamlit Cloud

Antes de hacer clic en "Deploy!", haz clic en **"Advanced settings"**.

En el campo **"Secrets"**, pega el siguiente bloque y reemplaza **todos** los valores entre comillas con los datos reales que obtuviste en los Bloques 1 y 2:

```toml
[database]
url = "postgresql://postgres:TU-CONTRASENA@db.TU-REF.supabase.co:5432/postgres"

[email]
smtp_host = "smtp.gmail.com"
smtp_port = 587
smtp_user = "tuusuario@gmail.com"
smtp_password = "xxxx xxxx xxxx xxxx"
from_address = "tuusuario@gmail.com"

[app]
secret_key = "genera-una-cadena-aleatoria-de-32-caracteres-aqui"
otp_ttl_minutes = 10
max_file_size_mb = 10
```

> **Sobre `secret_key`:** Debe ser una cadena aleatoria de al menos 32 caracteres. Puedes generarla en Python con:
> ```python
> import secrets; print(secrets.token_hex(32))
> ```
> O en [https://generate-secret.vercel.app/32](https://generate-secret.vercel.app/32).

### 4.3 Desplegar

Haz clic en **"Deploy!"**. Streamlit mostrara los logs de instalacion en tiempo real. El proceso tarda aproximadamente 2–3 minutos mientras instala las dependencias de `requirements.txt`. Cuando la app este lista, veras la pantalla de login.

---

## Bloque 5 — Inicializar la base de datos (una sola vez)

Las tablas de la base de datos deben crearse antes de que alguien use la app. Este paso se ejecuta una sola vez desde tu maquina local.

### 5.1 Crear el archivo de secrets local

En la carpeta `deliverables/app/`, crea la carpeta `.streamlit/` si no existe, y dentro crea el archivo `secrets.toml` con los mismos valores que pusiste en Streamlit Cloud:

```
deliverables/app/.streamlit/secrets.toml
```

Contenido (reemplaza con los valores reales):

```toml
[database]
url = "postgresql://postgres:TU-CONTRASENA@db.TU-REF.supabase.co:5432/postgres"

[email]
smtp_host = "smtp.gmail.com"
smtp_port = 587
smtp_user = "tuusuario@gmail.com"
smtp_password = "xxxx xxxx xxxx xxxx"
from_address = "tuusuario@gmail.com"

[app]
secret_key = "la-misma-cadena-que-pusiste-en-streamlit-cloud"
otp_ttl_minutes = 10
max_file_size_mb = 10
```

> **Este archivo NUNCA debe subirse a GitHub.** Ya esta en el `.gitignore` del proyecto, pero verifica que no aparezca en `git status` antes de cualquier push futuro.

### 5.2 Instalar dependencias y ejecutar el script

Desde la terminal, con la carpeta `deliverables/app/` como directorio de trabajo:

```bash
pip install -r requirements.txt
python init_db.py
```

El script imprimira una lista de todas las tablas que creo. La salida esperada se ve asi:

```
Creating tables...
  OK  budget_lines
  OK  categories
  OK  expenses
  OK  import_jobs
  OK  import_rows
  OK  otp_tokens
  OK  projects
  OK  rooms
  OK  users

Seeding taxonomy categories...
Done. Database is ready.
```

### 5.3 Verificar en Supabase

1. Ve a tu proyecto en [https://supabase.com](https://supabase.com).
2. En la barra lateral izquierda, haz clic en **"Table Editor"**.
3. Debes ver las tablas listadas: `users`, `projects`, `categories`, `rooms`, `budget_lines`, `expenses`, `import_jobs`, `import_rows`, `otp_tokens`.

Si las tablas no aparecen, revisa el mensaje de error que imprimio `init_db.py` — el problema mas comun es una URI incorrecta en `secrets.toml`.

---

## Bloque 6 — Verificar que la app funciona

### 6.1 Abrir la URL publica

Streamlit Cloud muestra la URL publica de tu app despues del deploy. Tendra la forma:

```
https://AFISmm-construction-app-main-XXXXXX.streamlit.app
```

Abre esa URL en el navegador.

### 6.2 Recorrer el flujo completo

Ejecuta estas 4 verificaciones en orden:

**1. Autenticacion OTP**
- En la pantalla de login, ingresa tu email.
- Haz clic en "Enviar codigo" (o "Send code").
- Revisa tu bandeja de entrada — debe llegar un correo con un codigo de 6 digitos en menos de 1 minuto.
- Ingresa el codigo en la app. Si el codigo es correcto, entras al dashboard.

**2. Crear un proyecto**
- En la barra lateral, haz clic en "Nuevo proyecto".
- Completa el formulario con un nombre de proyecto y haz clic en Guardar.
- El proyecto debe aparecer en el selector de la barra lateral.

**3. Ingresar una linea de presupuesto**
- Ve a la seccion "Presupuesto" en el menu.
- Agrega una linea de presupuesto con una categoria, monto y descripcion.
- Verifica que la linea aparece en la lista.

**4. Cambiar idioma**
- Usa el selector de idioma en la barra lateral para cambiar entre Espanol (ES) e Ingles (EN).
- Todos los textos de la interfaz deben cambiar de idioma.

### 6.3 Si algo falla

1. En Streamlit Cloud, busca tu app en el dashboard.
2. Haz clic en los tres puntos (...) junto al nombre de la app y selecciona **"Manage app"**.
3. En la parte inferior de la pantalla aparece una consola de logs. Los mensajes de error ahi explican el problema.
4. Consulta la seccion de Troubleshooting al final de esta guia.

---

## Bloque 7 — Actualizaciones futuras

Cada vez que hagas cambios en el codigo, el flujo para actualizar la app es:

```bash
git add .
git commit -m "Descripcion del cambio"
git push origin main
```

Streamlit Community Cloud detecta automaticamente el nuevo push y redespliega la app en 1–2 minutos. No necesitas hacer ningun paso adicional en Streamlit Cloud.

> **Si agregas una nueva dependencia Python**, asegurate de incluirla en `requirements.txt` antes del push. Si la dependencia no esta en `requirements.txt`, el redespliegue fallara con `ModuleNotFoundError`.

---

## Troubleshooting comun

| Sintoma | Causa probable | Solucion |
|---|---|---|
| `OperationalError: could not connect to server` | URL de Supabase incorrecta | Verificar la URI en los secrets de Streamlit Cloud (Bloque 4.2). Prestar atencion a caracteres especiales en la contrasena — codificarlos en URL si es necesario. |
| `ModuleNotFoundError` | Dependencia faltante en requirements.txt | Agregar la dependencia con su version al archivo `requirements.txt` y hacer push. |
| OTP no llega | Credenciales SMTP incorrectas | Verificar `smtp_user` y `smtp_password` en los secrets. Confirmar que la App Password de Gmail tiene exactamente 16 caracteres y que la verificacion en 2 pasos sigue activa en la cuenta. |
| App muestra error al arrancar | Tablas no inicializadas | Ejecutar `python init_db.py` desde local con el `secrets.toml` apuntando a la base de datos de Supabase (Bloque 5). |
| Datos no persisten entre sesiones | Sigue usando SQLite local | Verificar en `db.py` que el engine se construye con `st.secrets["database"]["url"]`. Si el `secrets.toml` local apunta a una base de datos SQLite, los datos solo se guardaran localmente. |
| `git push` pide usuario y contrasena repetidamente | GitHub ya no acepta contrasenas | Usar un Personal Access Token en lugar de la contrasena. Crearlo en: https://github.com/settings/tokens con scope `repo`. |
| Error `secrets not found` en la app | Secrets no configurados en Streamlit Cloud | Ir a Streamlit Cloud → Manage app → Settings → Secrets, y pegar el bloque TOML completo del Bloque 4.2. |
