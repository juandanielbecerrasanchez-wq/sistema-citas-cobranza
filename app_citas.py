import hmac
import streamlit as st
import pyodbc
from datetime import date, time
from html import escape

# --- Configuración de la página ---
st.set_page_config(
    page_title="Gestión de Citas - Cobranza",
    page_icon="📅",
    layout="wide"
)
ocultar_elementos_css = """
    <style>
    /* Ocultar barra superior (Fork, icono GitHub, menú) */
    header {visibility: hidden !important; display: none !important;}
    
    /* Ocultar pie de página clásico */
    footer {visibility: hidden !important; display: none !important;}
    
    /* Ocultar marca de agua y barra flotante inferior ("Hosted with Streamlit") */
    .stAppFooter {display: none !important; visibility: hidden !important;}
    div[data-testid="stStatusWidget"] {display: none !important; visibility: hidden !important;}
    div[data-testid="stDecoration"] {display: none !important;}
    div[data-testid="stToolbar"] {display: none !important;}
    #MainMenu {visibility: hidden !important;}
    
    /* Forzar ocultamiento de enlaces flotantes en esquinas inferiores */
    a[href*="streamlit.io"] {display: none !important;}
    [data-testid="stViewerBadge"] {display: none !important;}
    </style>
"""
st.markdown(ocultar_elementos_css, unsafe_allow_html=True)

PASSWORD_COBRANZA = "cobranza2026"

# --- Estilos visuales ---
st.markdown(
    """
    <style>
    :root {
        --canvas: #f3f6f4;
        --surface: #ffffff;
        --ink: #1c302b;
        --muted: #65766f;
        --primary: #176b5b;
        --primary-dark: #105346;
        --accent: #d47a45;
        --border: #dce5e0;
    }

    html, body, [data-testid="stAppViewContainer"],
    [data-testid="stHeader"] {
        background: var(--canvas);
        color: var(--ink);
    }

    .block-container {
        max-width: 1240px;
        padding-top: 2.2rem;
        padding-bottom: 3rem;
    }

    .hero {
        border-left: 5px solid var(--accent);
        padding: 0.35rem 0 0.35rem 1.2rem;
        margin-bottom: 1.8rem;
    }

    .hero h1 {
        margin: 0;
        font-size: 1.9rem;
        line-height: 1.25;
        color: var(--ink);
    }

    .hero p {
        margin: 0.5rem 0 0 0;
        color: var(--muted);
        font-size: 0.98rem;
    }

    .metric-card {
        background: var(--surface);
        border: 1px solid var(--border);
        border-top: 3px solid var(--primary);
        border-radius: 6px;
        padding: 1rem 1.1rem 0.9rem;
        height: 100%;
    }

    .metric-card .label {
        color: var(--muted);
        font-size: 0.82rem;
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }

    .metric-card .value {
        font-size: 1.8rem;
        font-weight: 700;
        color: var(--ink);
        margin-top: 0.2rem;
    }

    .panel {
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: 6px;
        padding: 0.9rem 1rem;
        color: var(--ink);
    }

    .section-title {
        font-size: 1.2rem;
        font-weight: 700;
        margin-bottom: 0.8rem;
        color: var(--ink);
    }

    .appointment-card {
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: 6px;
        padding: 0.8rem 1rem;
    }

    .appointment-card strong {
        color: var(--ink);
    }

    .stTabs [role="tablist"] {
        gap: 1rem;
        border-bottom: 1px solid var(--border);
    }

    .stTabs [role="tab"] {
        color: var(--muted);
        padding: 0.7rem 0.3rem;
    }

    .stTabs [role="tab"][aria-selected="true"] {
        color: var(--primary-dark);
        font-weight: 700;
    }

    [data-testid="stFormSubmitButton"] button,
    [data-testid="stButton"] button {
        min-height: 2.6rem;
        border-radius: 6px;
        font-weight: 700;
        padding: 0.55rem 1.1rem;
        transition: background-color 140ms ease, border-color 140ms ease;
    }

    [data-testid="stFormSubmitButton"] button[kind="primary"],
    [data-testid="stButton"] button[kind="primary"] {
        border: 1px solid var(--primary);
        background: var(--primary);
        color: white;
    }

    [data-testid="stFormSubmitButton"] button[kind="primary"]:hover,
    [data-testid="stButton"] button[kind="primary"]:hover {
        background: var(--primary-dark);
        border-color: var(--primary-dark);
    }

    [data-testid="stFormSubmitButton"] button:focus-visible,
    [data-testid="stButton"] button:focus-visible {
        outline: 3px solid rgba(212, 122, 69, 0.45);
        outline-offset: 2px;
    }

    .stSuccess, .stWarning, .stInfo {
        border-radius: 6px;
    }

    .stTextInput > div > div > input,
    .stDateInput > div > div > input,
    .stTimeInput > div > div > input,
    .stNumberInput > div > div > input {
        background: var(--surface);
        color: var(--ink);
        border: 1px solid var(--border);
        border-radius: 6px;
    }

    [data-testid="stForm"] {
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: 6px;
        padding: 1.2rem;
    }

    @media (max-width: 640px) {
        .block-container { padding-top: 1.2rem; }
        .hero h1 { font-size: 1.5rem; }
        [data-testid="stForm"] { padding: 0.8rem; }
    }
    </style>
    """,
    unsafe_allow_html=True
)

# --- Configuración de conexión a SQL Server (Somee) ---
SERVER = "CBTis139.mssql.somee.com"
DATABASE = "CBTis139"
USERNAME = "TovarLara_SQLLogin_1"
PASSWORD = "1hmetvyyiv"

def get_connection():
    available_drivers = set(pyodbc.drivers())
    driver = next(
        (
            name
            for name in (
                "ODBC Driver 18 for SQL Server",
                "ODBC Driver 17 for SQL Server",
                "SQL Server"
            )
            if name in available_drivers
        ),
        None
    )
    if driver is None:
        raise RuntimeError("Instala el controlador ODBC para SQL Server.")

    connection_string = (
        f"DRIVER={{{driver}}};"
        f"SERVER={SERVER};"
        f"DATABASE={DATABASE};"
        f"UID={USERNAME};"
        f"PWD={PASSWORD};"
        "TrustServerCertificate=yes;"
    )
    return pyodbc.connect(connection_string)

# --- Funciones auxiliares ---
def limpiar_texto(texto: str) -> str:
    return " ".join(texto.strip().split())

def asegurar_columna_estado(cursor) -> None:
    cursor.execute(
        """
        IF OBJECT_ID('dbo.citas', 'U') IS NULL
        BEGIN
            CREATE TABLE dbo.citas (
                id INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
                nombre NVARCHAR(120) NOT NULL,
                matricula NVARCHAR(30) NULL,
                carrera NVARCHAR(80) NULL,
                fecha DATE NOT NULL,
                hora TIME(0) NOT NULL,
                estado NVARCHAR(20) NOT NULL DEFAULT N'Pendiente'
            );
        END;
        IF COL_LENGTH('dbo.citas', 'matricula') IS NULL
        BEGIN
            ALTER TABLE dbo.citas ADD matricula NVARCHAR(30) NULL;
        END;
        IF COL_LENGTH('dbo.citas', 'carrera') IS NULL
        BEGIN
            ALTER TABLE dbo.citas ADD carrera NVARCHAR(80) NULL;
        END;
        IF COL_LENGTH('dbo.citas', 'estado') IS NULL
        BEGIN
            ALTER TABLE dbo.citas ADD estado NVARCHAR(20) NOT NULL
                DEFAULT N'Pendiente' WITH VALUES;
        END
        """
    )

def guardar_cita(matricula: str, carrera: str, fecha, hora) -> bool:
    matricula = limpiar_texto(matricula).upper()
    carrera = limpiar_texto(carrera)
    if not matricula or not carrera:
        st.warning("Completa la matrícula y la carrera para continuar.")
        return False

    if fecha < date.today():
        st.warning("No puedes agendar una cita en una fecha pasada.")
        return False

    if hora < time(8, 30) or hora > time(15, 30):
        st.warning("El horario de atención es de 8:30 AM a 3:30 PM.")
        return False

    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        asegurar_columna_estado(cursor)

        cursor.execute(
            "SELECT id FROM citas WHERE fecha = ? AND hora = ?",
            (fecha, hora)
        )
        if cursor.fetchone():
            st.warning("Ya existe una cita registrada para esa fecha y hora. Elige otro horario.")
            conn.close()
            return False

        cursor.execute(
            "INSERT INTO citas (nombre, matricula, carrera, fecha, hora, estado) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (f"{matricula} | {carrera}", matricula, carrera, fecha, hora, "Pendiente")
        )
        conn.commit()
        return True

    except Exception as e:
        st.error(f"Error al guardar la cita: {e}")
        return False
    finally:
        if conn is not None:
            conn.close()

def confirmar_cita(id_cita: int) -> bool:
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        asegurar_columna_estado(cursor)
        cursor.execute(
            "UPDATE citas SET estado = ? WHERE id = ?",
            ("Confirmada", id_cita)
        )
        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
        st.error(f"Error al confirmar la cita: {e}")
        return False
    finally:
        if conn is not None:
            conn.close()

@st.cache_data(ttl=30)
def obtener_citas():
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        asegurar_columna_estado(cursor)
        cursor.execute(
            "SELECT id, nombre, matricula, carrera, fecha, hora, estado "
            "FROM citas ORDER BY fecha ASC, hora ASC"
        )
        rows = cursor.fetchall()
        return rows
    except Exception as e:
        st.error(f"Error al obtener las citas: {e}")
        return []
    finally:
        if conn is not None:
            conn.close()

def separar_datos_alumno(registro: str, matricula: str = None, carrera: str = None):
    if matricula and carrera:
        return matricula, carrera
    if " | " in registro:
        return tuple(registro.split(" | ", 1))
    return registro, "Registro anterior"

def obtener_resumen(citas):
    total = len(citas)
    hoy = date.today()
    citas_hoy = sum(1 for _, _, _, _, fecha, _, _ in citas if fecha == hoy)
    citas_pendientes = sum(1 for _, _, _, _, _, _, estado in citas if estado != "Confirmada")

    return {
        "total": total,
        "hoy": citas_hoy,
        "pendientes": citas_pendientes
    }

# --- Encabezado ---
st.markdown(
    """
    <div class="hero">
        <h1>Gestión de citas de cobranza</h1>
        <p>Agenda y consulta turnos para el pago de colegiaturas.</p>
    </div>
    """,
    unsafe_allow_html=True
)

# --- Tabs principales ---
tab_alumno, tab_cobranza = st.tabs(["🎓 Agendar Cita", "💼 Panel de Cobranza"])

# --- TAB 1: ALUMNO ---
with tab_alumno:
    st.markdown('<div class="section-title">Nueva cita</div>', unsafe_allow_html=True)
    st.caption("Registra tus datos escolares y elige un horario disponible.")

    with st.form("form_cita", clear_on_submit=True):
        st.markdown("#### Datos del alumno")
        col_matricula, col_carrera = st.columns(2)

        with col_matricula:
            matricula = st.text_input("Matrícula", placeholder="Ej. 24A01234", max_chars=30)

        with col_carrera:
            carrera = st.text_input(
                "Carrera",
                placeholder="Ej. Técnico en Programación",
                max_chars=80
            )

        st.markdown("#### Fecha y horario")
        col_fecha, col_hora = st.columns(2)

        with col_fecha:
            fecha = st.date_input("Fecha de la cita", min_value=date.today(), value=date.today())

        with col_hora:
            hora = st.time_input("Hora de atención", value=time(8, 30))

        st.markdown(
            """
            <div class="panel">
                <strong>Horario de atención:</strong> 8:30 AM a 3:30 PM
            </div>
            """,
            unsafe_allow_html=True
        )

        submit_button = st.form_submit_button(
            "Agendar cita",
            type="primary",
            icon=":material/event_available:",
            use_container_width=True
        )

    if submit_button:
        if not matricula.strip() or not carrera.strip():
            st.warning("Escribe tu matrícula y carrera para registrar la cita.")
        else:
            exito = guardar_cita(matricula, carrera, fecha, hora)
            if exito:
                st.success(
                    f"Cita registrada para la matrícula {matricula.strip().upper()} "
                    f"({limpiar_texto(carrera)}) el {fecha} a las {hora.strftime('%H:%M')}."
                )
                st.cache_data.clear()

# --- TAB 2: COBRANZA ---
with tab_cobranza:
    if not st.session_state.get("cobranza_autorizada", False):
        with st.form("form_login_cobranza"):
            password_ingresada = st.text_input(
                "Contraseña de cobranza",
                type="password"
            )
            ingresar = st.form_submit_button("Ingresar", type="primary")

        if ingresar:
            if hmac.compare_digest(password_ingresada, PASSWORD_COBRANZA):
                st.session_state["cobranza_autorizada"] = True
                st.rerun()

        st.warning("Se requiere autorización para acceder al Panel de Cobranza.")
        st.stop()

    citas = obtener_citas()
    resumen = obtener_resumen(citas)

    st.markdown('<div class="section-title">Resumen de atención</div>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="label">Total</div>
                <div class="value">{resumen["total"]}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col2:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="label">Hoy</div>
                <div class="value">{resumen["hoy"]}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col3:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="label">Pendientes</div>
                <div class="value">{resumen["pendientes"]}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.write("")

    if not citas:
        st.info("No hay citas registradas en el sistema.")
    else:
        for cita in citas:
            (
                id_cita,
                registro_alumno,
                matricula_guardada,
                carrera_guardada,
                fecha_cita,
                hora_cita,
                estado_cita,
            ) = cita
            matricula_alumno, carrera_alumno = separar_datos_alumno(
                registro_alumno,
                matricula_guardada,
                carrera_guardada
            )
            matricula_segura = escape(matricula_alumno)
            carrera_segura = escape(carrera_alumno)
            hora_texto = hora_cita.strftime("%H:%M") if hasattr(hora_cita, "strftime") else str(hora_cita)

            with st.expander(f"🎓 {matricula_alumno} · {fecha_cita} · {hora_texto}", expanded=False):
                st.markdown(
                    f"""
                    <div class="appointment-card">
                        <p><strong>ID de cita:</strong> {id_cita}</p>
                        <p><strong>Matrícula:</strong> {matricula_segura}</p>
                        <p><strong>Carrera:</strong> {carrera_segura}</p>
                        <p><strong>Fecha:</strong> {fecha_cita}</p>
                        <p><strong>Hora:</strong> {hora_texto}</p>
                        <p><strong>Estado:</strong> {escape(estado_cita)}</p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                if estado_cita != "Confirmada":
                    if st.button(
                        "Confirmar cita",
                        key=f"confirmar_{id_cita}",
                        type="primary",
                        icon=":material/task_alt:"
                    ):
                        if confirmar_cita(id_cita):
                            st.cache_data.clear()
                            st.rerun()

                st.markdown("### 🔔 Enviar recordatorio")
                col_tiempo, col_boton = st.columns([2, 1])

                with col_tiempo:
                    minutos = st.number_input(
                        "Minutos restantes para el turno:",
                        min_value=5,
                        max_value=120,
                        value=15,
                        step=5,
                        key=f"min_{id_cita}"
                    )

                with col_boton:
                    if st.button(
                        "Generar aviso",
                        key=f"btn_{id_cita}",
                        icon=":material/notifications_active:"
                    ):
                        mensaje = (
                            f"Le recordamos que la cita de la matrícula {matricula_alumno} "
                            f"({carrera_alumno}) para el pago "
                            f"de colegiatura es en {minutos} minutos. Por favor pase al área de cobranza."
                        )
                        st.info(f"**Mensaje generado:**\n\n> {mensaje}")
