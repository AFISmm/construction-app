# Manual de Usuario — ConstructionApp

## ¿Qué es ConstructionApp?

ConstructionApp es una herramienta en línea para controlar el presupuesto y los gastos de proyectos de construcción o remodelación. Permite registrar líneas de presupuesto por categoría, ingresar gastos, visualizar el avance de ejecución y generar reportes. Está diseñada para gerentes de proyecto y propietarios que necesitan tener el control del dinero en todo momento, sin necesidad de conocimientos técnicos.

---

## Cómo acceder

1. Abre tu navegador y ve a `https://constructionapp.streamlit.app`.
2. Escribe tu **Correo electronico** en el campo correspondiente.
3. Escribe tu **Contrasena** y haz clic en **Ingresar**.
4. Si es tu primera vez, haz clic en la pestaña **Crear cuenta**, completa el formulario y haz clic en **Registrarse**.

> ⚠️ Las cuentas nuevas quedan pendientes de aprobación. Recibirás acceso una vez que el administrador apruebe tu solicitud.

> 💡 Si olvidaste tu contraseña, contacta al administrador del sistema.

---

## Gestión de proyectos

### Ver tus proyectos

1. En la barra lateral izquierda, haz clic en **Proyectos**.
2. Verás la lista de todos tus proyectos con el **Presupuesto total** y el **% Ejecutado** de cada uno.
3. Para activar un proyecto, haz clic en **Seleccionar** junto al nombre del proyecto que quieres trabajar.

### Crear un proyecto nuevo

1. Haz clic en **+ Nuevo proyecto** en la barra lateral.
2. Escribe el **Nombre del proyecto** (por ejemplo: "Remodelacion Casa Bogota").
3. Selecciona el **Tipo de proyecto**: Residencial o Comercial.
4. Agrega una **Descripcion** si lo deseas.
5. Haz clic en **Crear proyecto**.

### Editar un proyecto

1. Ve a **Proyectos** en la barra lateral.
2. Ubica el proyecto que quieres modificar y haz clic en **Editar**.
3. Realiza los cambios y haz clic en **Guardar**.

> ⚠️ Eliminar un proyecto borrará todos sus datos de forma permanente y no se puede deshacer.

---

## Presupuesto

1. Asegúrate de tener un **Proyecto activo** seleccionado en la barra lateral.
2. Haz clic en **Presupuesto** en la barra lateral.
3. Haz clic en el panel **Agregar linea** para desplegarlo.
4. Selecciona la **Categoria** (por ejemplo: "Instalaciones Electricas").
5. Si aplica, selecciona la **Habitacion** asociada o deja **Todo el proyecto**.
6. Escribe una **Descripcion** opcional para identificar la línea.
7. Ingresa el **Monto presupuestado**.
8. Haz clic en **Guardar**.

> 💡 Las líneas de presupuesto están organizadas por categorías principales (Adquisicion del Bien, Costos Blandos, Presupuesto de Construccion, etc.). Elige la categoría que mejor describe el rubro.

---

## Gastos

1. Haz clic en **Gastos** en la barra lateral.
2. Ubica la línea de presupuesto sobre la que quieres registrar el gasto.
3. Haz clic en **Registrar gasto** junto a esa línea.
4. Completa los campos: **Proveedor**, **Descripcion**, **Monto**, **Fecha** y **Notas** (opcional).
5. Haz clic en **Guardar**.

> ⚠️ Si el gasto supera el monto presupuestado de la línea, verás el aviso "Esta categoria supera el presupuesto". Revisa el valor antes de confirmar.

---

## Reportes y progreso

1. Haz clic en **Progreso** en la barra lateral.
2. Verás la barra de **Ejecucion total del proyecto** con el porcentaje ejecutado hasta el momento.
3. El gráfico **Presupuesto vs. Ejecutado por categoria** muestra, para cada categoría, el monto presupuestado frente al ejecutado.
4. La tabla de varianza muestra la columna **Variacion** por categoría (positivo = bajo presupuesto, negativo = sobre presupuesto).
5. Para exportar los datos, haz clic en **Exportar CSV** o **Exportar Excel**.

> 💡 Usa la exportación a Excel para compartir el reporte con el cliente o el equipo de obra.

---

## Importar un archivo

1. Haz clic en **Importar** en la barra lateral.
2. Selecciona cómo quieres importar: **Importar nuevo** (crea líneas nuevas) o **Importar en el mismo proyecto** (combina con las líneas existentes).
3. Haz clic en **Selecciona archivo** y elige un archivo `.xlsx`, `.xls` o `.csv` desde tu computador.
4. La app mostrará una **Vista previa** con cuatro columnas: **Descripcion original**, **Categoria asignada**, **Confianza** y **Corregir**.
5. Revisa las filas marcadas (baja confianza). Si la categoría asignada no es correcta, usa el menú **Corregir** para cambiarla.
6. Cuando todas las filas estén revisadas, haz clic en **Confirmar importacion**.

> ⚠️ No podrás confirmar la importación mientras haya filas marcadas sin revisar. El sistema te mostrará el mensaje "Revisa todas las filas marcadas antes de confirmar."

---

## Cambiar idioma

Los botones **ES** y **EN** aparecen en la esquina superior derecha de cualquier pantalla.

1. Haz clic en **ES** para cambiar la interfaz a español.
2. Haz clic en **EN** para cambiar la interfaz a inglés.

El idioma seleccionado se mantiene durante toda la sesión.

---

## Cerrar sesión

1. En la barra lateral, desplázate hasta el final.
2. Haz clic en **Cerrar sesion**.
3. Serás redirigido a la pantalla de inicio de sesión.

> 💡 Cierra siempre la sesión si usas un dispositivo compartido o público.

---

## Cómo convertir este documento a PDF

**Opción 1 — Google Docs:**
1. Abre docs.google.com → Nuevo documento
2. Copia y pega el contenido de este archivo
3. Archivo → Descargar → PDF

**Opción 2 — VS Code:**
Instala la extensión "Markdown PDF" → clic derecho en el archivo → "Export (pdf)"
