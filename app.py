"""Versión Flask y SQLite para ejecutar el curso sin instalar MySQL."""
from __future__ import annotations

import csv
import hashlib
import io
import json
import os
import re
import secrets
import sqlite3
from datetime import datetime
from functools import wraps
from pathlib import Path

from flask import Flask, abort, flash, g, jsonify, make_response, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

BASE_DIR = Path(__file__).resolve().parent
INSTANCE_DIR = BASE_DIR / "instance"
DATABASE = INSTANCE_DIR / "aprende_informatica.sqlite3"
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

app = Flask(__name__, static_folder="assets", static_url_path="/assets")
app.config.update(
    SECRET_KEY=os.environ.get("FLASK_SECRET_KEY", secrets.token_hex(32)),
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=os.environ.get("FLASK_HTTPS_ONLY") == "1",
)

LECCIONES = [
    ("¿Qué es la informática?", "Descubre cómo usamos la información con ayuda de la tecnología.", "La informática estudia cómo representar, guardar, procesar y compartir información usando computadores y otros dispositivos. Está presente cuando escribes un mensaje, buscas una dirección o guardas una fotografía.\n\nEjemplo: al enviar un correo, el computador organiza tus palabras y las transmite por internet.", "💡"),
    ("Componentes del computador", "Conoce las partes que trabajan juntas en un computador.", "Un computador tiene componentes que puedes tocar, como el teclado y la pantalla, y componentes internos que procesan y guardan información. La CPU ejecuta instrucciones; la memoria RAM ayuda mientras trabajas.\n\nEjemplo: el teclado sirve para escribir y el monitor para ver lo que ocurre.", "🖥️"),
    ("Hardware y software", "Diferencia las partes físicas de los programas.", "Hardware es cada parte física del equipo: ratón, pantalla o disco. Software son los programas e instrucciones, como un navegador o un editor de texto. Se necesitan mutuamente para que el computador sea útil.\n\nEjemplo: puedes tocar el teclado (hardware), pero no el procesador de textos (software).", "⚙️"),
    ("Sistema operativo", "Aprende para qué sirve el sistema operativo.", "El sistema operativo coordina el computador y permite abrir aplicaciones, organizar archivos y usar dispositivos. Windows, macOS, Linux y Android son ejemplos.\n\nEjemplo: cuando abres una aplicación, el sistema operativo ayuda a que funcione y muestra su ventana.", "🧭"),
    ("Archivos y carpetas", "Organiza tus documentos para encontrarlos fácilmente.", "Un archivo guarda información, como un texto, una imagen o una presentación. Las carpetas agrupan archivos y otras carpetas. Pon nombres claros y guarda cada documento en un lugar fácil de recordar.\n\nEjemplo: crea una carpeta llamada Informática y dentro guarda una actividad con su fecha.", "📁"),
    ("Uso seguro de internet", "Cuida tus datos y toma decisiones seguras en línea.", "Internet permite aprender y comunicarnos. Protege tus contraseñas, no compartas datos personales con desconocidos y verifica los enlaces antes de abrirlos. Si algo te preocupa, consulta a una persona de confianza.\n\nEjemplo: una institución nunca debería pedirte tu contraseña por un mensaje inesperado.", "🔒"),
    ("Herramientas ofimáticas básicas", "Crea documentos, organiza datos y presenta tus ideas.", "Word permite escribir documentos; Excel organiza datos en celdas y puede hacer cálculos; PowerPoint permite crear presentaciones con diapositivas.\n\nEjemplo: redacta un informe en Word, lleva una lista de gastos en Excel y explica un tema en PowerPoint.", "📝"),
]

# Cada pregunta contiene enunciado, cuatro opciones, clave correcta y explicación.
PREGUNTAS = [
    (1, "¿Qué estudia principalmente la informática?", ["Cómo procesar y organizar información con tecnología", "Cómo cultivar plantas", "Cómo construir carreteras", "Cómo preparar alimentos"], "a", "La informática trabaja con información usando computadores y otros dispositivos."),
    (1, "¿Cuál es un ejemplo cotidiano de informática?", ["Enviar un mensaje desde el teléfono", "Regar una planta a mano", "Doblar una hoja", "Pintar una pared"], "a", "Al enviar un mensaje, un dispositivo procesa y transmite información."),
    (1, "¿Qué puede ayudarnos a hacer un computador?", ["Guardar y procesar información", "Hacer que nunca necesitemos aprender", "Reemplazar todas las decisiones", "Funcionar sin energía"], "a", "Los computadores ayudan a organizar y procesar información."),
    (1, "¿Qué ocurre al guardar una fotografía?", ["La información se almacena como un archivo", "La pantalla se convierte en cámara", "Se borra internet", "El teclado guarda la foto"], "a", "La fotografía queda almacenada como un archivo digital."),
    (1, "¿Cuál actividad usa tecnología informática?", ["Buscar una dirección con un mapa digital", "Caminar por un sendero sin dispositivos", "Escribir en la arena", "Mirar una nube"], "a", "Una aplicación de mapas procesa datos para mostrar rutas."),
    (2, "¿Cuál componente permite escribir texto?", ["Teclado", "Monitor", "Parlante", "Impresora"], "a", "El teclado permite introducir letras, números y comandos."),
    (2, "¿Qué componente muestra imágenes y texto?", ["Monitor", "Ratón", "Micrófono", "Disco externo"], "a", "El monitor es una pantalla de salida visual."),
    (2, "¿Qué componente ejecuta instrucciones del computador?", ["Procesador (CPU)", "Altavoz", "Teclado", "Cámara web"], "a", "El procesador ejecuta instrucciones y coordina tareas."),
    (2, "¿Para qué sirve la memoria RAM?", ["Mantener datos temporalmente mientras trabajas", "Imprimir documentos", "Conectar el cable de corriente", "Mostrar colores en la pantalla"], "a", "La RAM guarda temporalmente la información de las tareas abiertas."),
    (2, "¿Cuál es un dispositivo de entrada?", ["Ratón", "Monitor", "Parlante", "Proyector"], "a", "El ratón envía movimientos y selecciones al computador."),
    (3, "¿Qué significa hardware?", ["Las partes físicas que podemos tocar", "Los programas del equipo", "Una conexión a internet", "Una carpeta de documentos"], "a", "Hardware son los componentes físicos del computador."),
    (3, "¿Cuál opción es software?", ["Un navegador web", "Un teclado", "Un monitor", "Un cable USB"], "a", "El navegador es un programa: por eso es software."),
    (3, "¿Cuál opción es hardware?", ["Ratón", "Procesador de textos", "Sistema operativo", "Videojuego"], "a", "El ratón es un componente físico."),
    (3, "¿Qué necesita el software para funcionar?", ["Un dispositivo de hardware", "Una hoja de papel", "Una carpeta vacía", "Un lápiz"], "a", "Los programas se ejecutan en dispositivos físicos."),
    (3, "¿Puedes tocar físicamente una aplicación?", ["No, es un programa", "Sí, como un teclado", "Sí, como una pantalla", "Solo cuando está apagada"], "a", "Una aplicación es software, no una parte física."),
    (4, "¿Qué hace un sistema operativo?", ["Coordina el equipo y permite usar aplicaciones", "Imprime sin impresora", "Crea electricidad", "Limpia físicamente la pantalla"], "a", "El sistema operativo coordina recursos y permite ejecutar programas."),
    (4, "¿Cuál es un sistema operativo?", ["Windows", "Un teclado", "Una carpeta", "Una hoja de cálculo"], "a", "Windows es un sistema operativo para computadores."),
    (4, "¿Quién ayuda a abrir y organizar aplicaciones?", ["El sistema operativo", "El cable de red", "El monitor apagado", "La mesa"], "a", "El sistema operativo administra aplicaciones y recursos del equipo."),
    (4, "¿Android se usa como sistema operativo en muchos...?", ["Teléfonos y tabletas", "Teclados", "Impresoras de papel", "Cables"], "a", "Android es común en teléfonos y tabletas."),
    (4, "¿Qué sucede cuando abres una aplicación?", ["El sistema operativo ayuda a ejecutarla", "Se apaga el procesador", "Se borra el archivo", "Se desconecta la pantalla"], "a", "El sistema operativo coordina la ejecución de la aplicación."),
    (5, "¿Qué es un archivo?", ["Un elemento que guarda información", "Un dispositivo para escuchar música", "Una conexión inalámbrica", "Un tipo de teclado"], "a", "Un archivo almacena información como texto o imágenes."),
    (5, "¿Para qué sirve una carpeta?", ["Para agrupar y organizar archivos", "Para aumentar el brillo", "Para escribir una contraseña", "Para navegar por internet"], "a", "Las carpetas ayudan a mantener juntos documentos relacionados."),
    (5, "¿Qué nombre facilita encontrar una tarea?", ["Actividad de informática - 13 octubre", "Documento nuevo final final", "asdf", "Sin título"], "a", "Un nombre descriptivo permite reconocer el archivo después."),
    (5, "¿Dónde podrías guardar varias tareas de informática?", ["En una carpeta llamada Informática", "En la papelera", "En el fondo de pantalla", "En el teclado"], "a", "Una carpeta temática agrupa documentos del mismo tema."),
    (5, "¿Qué puede contener una carpeta?", ["Archivos y otras carpetas", "Solo conexiones a internet", "Únicamente el sistema operativo", "Solo contraseñas"], "a", "Las carpetas pueden organizar archivos y subcarpetas."),
    (6, "¿Qué debes hacer con tu contraseña?", ["Mantenerla privada", "Publicarla en redes sociales", "Compartirla con desconocidos", "Usar la misma en carteles públicos"], "a", "Una contraseña privada protege tus cuentas."),
    (6, "¿Qué hacer con un enlace inesperado que pide tus datos?", ["No abrirlo y consultarlo con alguien de confianza", "Escribir tu contraseña enseguida", "Reenviarlo a todo el curso", "Descargar todos sus archivos"], "a", "Los enlaces inesperados pueden ser engañosos; consulta antes de actuar."),
    (6, "¿Qué dato conviene proteger en internet?", ["Tu dirección y contraseña", "El nombre de un color", "La capital de un país", "El resultado de una suma"], "a", "La dirección y la contraseña son datos personales sensibles."),
    (6, "Si un mensaje en línea te hace sentir inseguridad, ¿qué haces?", ["Hablar con una persona de confianza", "Responder con más datos", "Guardar el secreto siempre", "Enviar tu ubicación"], "a", "Pedir ayuda a una persona de confianza es una decisión segura."),
    (6, "¿Cómo puedes revisar un enlace antes de abrirlo?", ["Comprobar quién lo envía y a dónde dirige", "Abrirlo rápido sin mirar", "Compartirlo primero", "Desactivar todas las protecciones"], "a", "Verificar el remitente y el destino ayuda a evitar engaños."),
    (7, "¿Para qué se usa principalmente Word?", ["Escribir documentos", "Hacer cálculos en celdas", "Crear diapositivas", "Conectar a internet"], "a", "Word es una herramienta para redactar y dar formato a documentos."),
    (7, "¿Qué herramienta organiza datos en celdas?", ["Excel", "Word", "PowerPoint", "Paint"], "a", "Excel organiza información en filas, columnas y celdas."),
    (7, "¿Qué programa permite crear diapositivas?", ["PowerPoint", "Excel", "Bloc de notas", "Calculadora"], "a", "PowerPoint sirve para organizar ideas en una presentación."),
    (7, "¿En qué herramienta podrías sumar una lista de gastos?", ["Excel", "PowerPoint", "Word", "Navegador"], "a", "Excel puede hacer cálculos con datos en celdas."),
    (7, "¿Qué herramienta elegirías para redactar un informe?", ["Word", "Excel", "PowerPoint", "Cámara"], "a", "Word es adecuado para redactar informes y documentos."),
]


def conectar_db() -> sqlite3.Connection:
    conexion = sqlite3.connect(DATABASE)
    conexion.row_factory = sqlite3.Row
    conexion.execute("PRAGMA foreign_keys = ON")
    return conexion


def obtener_db() -> sqlite3.Connection:
    if "db" not in g:
        g.db = conectar_db()
    return g.db


@app.teardown_appcontext
def cerrar_db(_error: Exception | None) -> None:
    conexion = g.pop("db", None)
    if conexion is not None:
        conexion.close()


def inicializar_db() -> None:
    INSTANCE_DIR.mkdir(exist_ok=True)
    conexion = conectar_db()
    conexion.executescript("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT NOT NULL, apellido TEXT NOT NULL,
            cedula TEXT NOT NULL UNIQUE, correo TEXT NOT NULL UNIQUE, contrasena TEXT NOT NULL,
            rol TEXT NOT NULL CHECK (rol IN ('estudiante', 'docente')),
            fecha_registro TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS estudiantes (
            id INTEGER PRIMARY KEY AUTOINCREMENT, usuario_id INTEGER NOT NULL UNIQUE,
            carrera TEXT NOT NULL, trayecto TEXT NOT NULL DEFAULT '', fecha_registro TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS lecciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT, titulo TEXT NOT NULL, descripcion TEXT NOT NULL,
            contenido TEXT NOT NULL, imagen TEXT NOT NULL DEFAULT '▣', orden INTEGER NOT NULL DEFAULT 1,
            estado TEXT NOT NULL DEFAULT 'publicada' CHECK (estado IN ('publicada', 'borrador'))
        );
        CREATE TABLE IF NOT EXISTS preguntas (
            id INTEGER PRIMARY KEY AUTOINCREMENT, leccion_id INTEGER NOT NULL, enunciado TEXT NOT NULL,
            opcion_a TEXT NOT NULL, opcion_b TEXT NOT NULL, opcion_c TEXT NOT NULL, opcion_d TEXT NOT NULL,
            respuesta_correcta TEXT NOT NULL CHECK (respuesta_correcta IN ('a', 'b', 'c', 'd')), explicacion TEXT NOT NULL,
            FOREIGN KEY (leccion_id) REFERENCES lecciones(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS resultados (
            id INTEGER PRIMARY KEY AUTOINCREMENT, estudiante_id INTEGER NOT NULL, leccion_id INTEGER NOT NULL,
            puntaje INTEGER NOT NULL, total_preguntas INTEGER NOT NULL, fecha TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (estudiante_id) REFERENCES estudiantes(id) ON DELETE CASCADE,
            FOREIGN KEY (leccion_id) REFERENCES lecciones(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS progreso (
            id INTEGER PRIMARY KEY AUTOINCREMENT, estudiante_id INTEGER NOT NULL, leccion_id INTEGER NOT NULL,
            porcentaje_completado INTEGER NOT NULL DEFAULT 0,
            estado TEXT NOT NULL DEFAULT 'pendiente' CHECK (estado IN ('pendiente', 'en_progreso', 'completada')),
            fecha_actualizacion TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE (estudiante_id, leccion_id),
            FOREIGN KEY (estudiante_id) REFERENCES estudiantes(id) ON DELETE CASCADE,
            FOREIGN KEY (leccion_id) REFERENCES lecciones(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS recuperaciones (
            usuario_id INTEGER PRIMARY KEY, token_hash TEXT NOT NULL, vence TEXT NOT NULL,
            FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
        );
    """)
    columnas_estudiantes = {fila["name"] for fila in conexion.execute("PRAGMA table_info(estudiantes)")}
    if "trayecto" not in columnas_estudiantes:
        conexion.execute("ALTER TABLE estudiantes ADD COLUMN trayecto TEXT NOT NULL DEFAULT ''")
        if "semestre" in columnas_estudiantes:
            conexion.execute("UPDATE estudiantes SET trayecto = semestre")
    if conexion.execute("SELECT COUNT(*) FROM lecciones").fetchone()[0] == 0:
        for orden, (titulo, descripcion, contenido, icono) in enumerate(LECCIONES, start=1):
            conexion.execute(
                "INSERT INTO lecciones (titulo, descripcion, contenido, imagen, orden) VALUES (?, ?, ?, ?, ?)",
                (titulo, descripcion, contenido, icono, orden),
            )
        for lesson_order, enunciado, opciones, correcta, explicacion in PREGUNTAS:
            lesson_id = lesson_order
            conexion.execute(
                "INSERT INTO preguntas (leccion_id, enunciado, opcion_a, opcion_b, opcion_c, opcion_d, respuesta_correcta, explicacion) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (lesson_id, enunciado, *opciones, correcta, explicacion),
            )
    clave_docente_inicial = os.environ.get("INITIAL_TEACHER_PASSWORD")
    if clave_docente_inicial is None and not os.environ.get("FLASK_SECRET_KEY"):
        clave_docente_inicial = "Docente2026!"
    if clave_docente_inicial is not None:
        if not 8 <= len(clave_docente_inicial.encode("utf-8")) <= 72:
            conexion.close()
            raise RuntimeError("INITIAL_TEACHER_PASSWORD debe tener entre 8 y 72 bytes.")
        conexion.execute(
            "INSERT OR IGNORE INTO usuarios (nombre, apellido, cedula, correo, contrasena, rol) VALUES (?, ?, ?, ?, ?, 'docente')",
            ("Docente", "UPTAIET", "V-00000001", "docente@uptaiet.edu.ve", generate_password_hash(clave_docente_inicial)),
        )
    conexion.commit()
    conexion.close()


def csrf_token() -> str:
    if "csrf" not in session:
        session["csrf"] = secrets.token_hex(32)
    return session["csrf"]


def csrf_valido() -> bool:
    enviado = request.form.get("csrf", "")
    guardado = session.get("csrf", "")
    return bool(enviado and guardado and secrets.compare_digest(enviado, guardado))


def correo_valido(correo: str) -> bool:
    return len(correo) <= 190 and bool(EMAIL_RE.fullmatch(correo))


def texto_valido(texto: str, maximo: int, multilinea: bool = False) -> bool:
    controles_permitidos = "\n\r\t" if multilinea else ""
    return bool(texto) and len(texto) <= maximo and not any(
        ord(caracter) < 32 and caracter not in controles_permitidos for caracter in texto
    )


def entero_formulario(campo: str, minimo: int, maximo: int) -> int | None:
    valor = request.form.get(campo, "")
    if not valor.isdecimal():
        return None
    numero = int(valor)
    return numero if minimo <= numero <= maximo else None


def login_requerido(rol: str | None = None):
    def decorar(vista):
        @wraps(vista)
        def protegida(*args, **kwargs):
            usuario = session.get("usuario")
            if not usuario:
                return redirect(url_for("login"))
            if rol and usuario["rol"] != rol:
                return redirect(url_for("inicio"))
            return vista(*args, **kwargs)
        return protegida
    return decorar


def obtener_lecciones(publicadas: bool = True) -> list[sqlite3.Row]:
    filtro = "WHERE estado = 'publicada'" if publicadas else ""
    return obtener_db().execute(f"SELECT * FROM lecciones {filtro} ORDER BY orden, id").fetchall()


def progreso_curso(estudiante_id: int) -> int:
    conexion = obtener_db()
    total = conexion.execute("SELECT COUNT(*) FROM lecciones WHERE estado='publicada'").fetchone()[0]
    hechas = conexion.execute("SELECT COUNT(*) FROM progreso p JOIN lecciones l ON l.id=p.leccion_id WHERE p.estudiante_id=? AND p.estado='completada' AND l.estado='publicada'", (estudiante_id,)).fetchone()[0]
    return round(hechas * 100 / total) if total else 0


@app.context_processor
def variables_comunes():
    return {"usuario": session.get("usuario"), "csrf": csrf_token}


@app.route("/")
def inicio():
    if not session.get("usuario"):
        return render_template("page.html", vista="portada")
    if session["usuario"]["rol"] == "docente":
        return redirect(url_for("panel_docente"))
    conexion = obtener_db()
    estudiante = conexion.execute("SELECT id FROM estudiantes WHERE usuario_id=?", (session["usuario"]["id"],)).fetchone()
    avance = progreso_curso(estudiante["id"])
    lecciones = obtener_lecciones()[:3]
    return render_template("page.html", vista="inicio", avance=avance, lecciones=lecciones)


@app.route("/registro", methods=["GET", "POST"])
def registro():
    if request.method == "POST":
        if not csrf_valido():
            abort(400, "El formulario venció. Recarga la página e inténtalo de nuevo.")
        datos = {campo: request.form.get(campo, "").strip() for campo in ("nombre", "apellido", "cedula", "correo", "carrera", "trayecto")}
        clave = request.form.get("contrasena", "")
        datos["correo"] = datos["correo"].lower()
        campos_validos = (
            texto_valido(datos["nombre"], 100)
            and texto_valido(datos["apellido"], 100)
            and texto_valido(datos["cedula"], 30)
            and texto_valido(datos["carrera"], 120)
            and datos["trayecto"] in {str(numero) for numero in range(5)}
            and correo_valido(datos["correo"])
            and 8 <= len(clave.encode("utf-8")) <= 72
        )
        if not campos_validos:
            flash("Revisa los campos: nombres, cédula y carrera son obligatorios; el correo debe ser válido y la contraseña debe tener entre 8 y 72 bytes.", "error")
            return render_template("page.html", vista="formulario", tipo="registro")
        conexion = obtener_db()
        try:
            cursor = conexion.execute("INSERT INTO usuarios (nombre, apellido, cedula, correo, contrasena, rol) VALUES (?, ?, ?, ?, ?, 'estudiante')", (datos["nombre"], datos["apellido"], datos["cedula"], datos["correo"], generate_password_hash(clave)))
            conexion.execute("INSERT INTO estudiantes (usuario_id, carrera, trayecto) VALUES (?, ?, ?)", (cursor.lastrowid, datos["carrera"], datos["trayecto"]))
            conexion.commit()
        except sqlite3.IntegrityError:
            conexion.rollback()
            flash("Ese correo o cédula ya está registrado.", "error")
            return render_template("page.html", vista="formulario", tipo="registro")
        session.clear()
        session["usuario"] = {"id": cursor.lastrowid, "nombre": datos["nombre"], "apellido": datos["apellido"], "rol": "estudiante"}
        return redirect(url_for("inicio"))
    return render_template("page.html", vista="formulario", tipo="registro")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if not csrf_valido():
            abort(400)
        correo = request.form.get("correo", "").strip().lower()
        contrasena = request.form.get("contrasena", "")
        cuenta = obtener_db().execute("SELECT * FROM usuarios WHERE correo=?", (correo,)).fetchone() if correo_valido(correo) else None
        if not cuenta or not check_password_hash(cuenta["contrasena"], contrasena):
            flash("El correo o la contraseña no coinciden.", "error")
        else:
            session.clear()
            session["usuario"] = {"id": cuenta["id"], "nombre": cuenta["nombre"], "apellido": cuenta["apellido"], "rol": cuenta["rol"]}
            return redirect(url_for("inicio"))
    return render_template("page.html", vista="formulario", tipo="login")


@app.route("/salir", methods=["POST"])
def salir():
    if not csrf_valido():
        abort(400)
    session.clear()
    return redirect(url_for("inicio"))


@app.route("/recuperar", methods=["GET", "POST"])
def recuperar():
    enlace = session.pop("enlace_recuperacion", None)
    if request.method == "POST":
        if not csrf_valido():
            abort(400)
        correo = request.form.get("correo", "").strip().lower()
        cuenta = obtener_db().execute("SELECT id FROM usuarios WHERE correo=?", (correo,)).fetchone() if correo_valido(correo) else None
        if cuenta:
            token = secrets.token_urlsafe(32)
            token_hash = hashlib.sha256(token.encode()).hexdigest()
            obtener_db().execute("INSERT INTO recuperaciones (usuario_id, token_hash, vence) VALUES (?, ?, datetime('now', '+30 minutes')) ON CONFLICT(usuario_id) DO UPDATE SET token_hash=excluded.token_hash, vence=excluded.vence", (cuenta["id"], token_hash))
            obtener_db().commit()
            session["enlace_recuperacion"] = url_for("nueva_clave", token=token)
        flash("Si la cuenta existe, se generó un enlace. En modo local aparece aquí; configura correo antes de publicar.", "exito")
        return redirect(url_for("recuperar"))
    return render_template("page.html", vista="formulario", tipo="recuperar", enlace=enlace)


@app.route("/nueva-clave/<token>", methods=["GET", "POST"])
def nueva_clave(token: str):
    if request.method == "POST":
        if not csrf_valido():
            abort(400)
        clave = request.form.get("contrasena", "")
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        recuperacion = obtener_db().execute("SELECT usuario_id FROM recuperaciones WHERE token_hash=? AND vence > datetime('now')", (token_hash,)).fetchone()
        if not 8 <= len(clave.encode("utf-8")) <= 72 or not recuperacion:
            flash("El enlace venció o la contraseña no tiene entre 8 y 72 bytes. Solicita otro enlace.", "error")
        else:
            conexion = obtener_db()
            conexion.execute("UPDATE usuarios SET contrasena=? WHERE id=?", (generate_password_hash(clave), recuperacion["usuario_id"]))
            conexion.execute("DELETE FROM recuperaciones WHERE usuario_id=?", (recuperacion["usuario_id"],))
            conexion.commit()
            flash("Contraseña actualizada. Ya puedes iniciar sesión.", "exito")
            return redirect(url_for("login"))
    return render_template("page.html", vista="formulario", tipo="nueva-clave", token=token)


@app.route("/lecciones")
@login_requerido()
def lecciones():
    return render_template("page.html", vista="lecciones", lecciones=obtener_lecciones())


@app.route("/leccion/<int:lesson_id>", methods=["GET", "POST"])
@login_requerido("estudiante")
def leccion(lesson_id: int):
    conexion = obtener_db()
    lesson = conexion.execute("SELECT * FROM lecciones WHERE id=? AND estado='publicada'", (lesson_id,)).fetchone()
    if not lesson:
        abort(404)
    if request.method == "POST":
        if not csrf_valido():
            return jsonify(ok=False, error="La sesión venció. Recarga la lección e inténtalo de nuevo."), 400
        try:
            respuestas = json.loads(request.form.get("respuestas", "{}"))
        except json.JSONDecodeError:
            return jsonify(ok=False, error="No pudimos leer tus respuestas."), 400
        preguntas = conexion.execute("SELECT id, respuesta_correcta FROM preguntas WHERE leccion_id=? ORDER BY id", (lesson_id,)).fetchall()
        ids_preguntas = {str(p["id"]) for p in preguntas}
        if (
            len(preguntas) != 5
            or not isinstance(respuestas, dict)
            or set(respuestas) != ids_preguntas
            or any(respuestas.get(str(p["id"])) not in ("a", "b", "c", "d") for p in preguntas)
        ):
            return jsonify(ok=False, error="Responde las cinco preguntas antes de enviar."), 400
        estudiante = conexion.execute("SELECT id FROM estudiantes WHERE usuario_id=?", (session["usuario"]["id"],)).fetchone()
        if not estudiante:
            return jsonify(ok=False, error="No encontramos el perfil de estudiante asociado a tu cuenta."), 400
        aciertos = sum(respuestas[str(p["id"])] == p["respuesta_correcta"] for p in preguntas)
        conexion.execute("INSERT INTO resultados (estudiante_id, leccion_id, puntaje, total_preguntas) VALUES (?, ?, ?, ?)", (estudiante["id"], lesson_id, aciertos, len(preguntas)))
        conexion.execute("INSERT INTO progreso (estudiante_id, leccion_id, porcentaje_completado, estado) VALUES (?, ?, 100, 'completada') ON CONFLICT(estudiante_id, leccion_id) DO UPDATE SET porcentaje_completado=100, estado='completada', fecha_actualizacion=CURRENT_TIMESTAMP", (estudiante["id"], lesson_id))
        conexion.commit()
        return jsonify(ok=True, aciertos=aciertos, total=len(preguntas), porcentaje=round(aciertos * 100 / len(preguntas)))
    preguntas = [dict(p) for p in conexion.execute("SELECT * FROM preguntas WHERE leccion_id=? ORDER BY id", (lesson_id,)).fetchall()]
    return render_template("page.html", vista="leccion", leccion=lesson, preguntas=preguntas)


@app.route("/progreso")
@login_requerido("estudiante")
def mi_progreso():
    conexion = obtener_db()
    estudiante = conexion.execute("SELECT id FROM estudiantes WHERE usuario_id=?", (session["usuario"]["id"],)).fetchone()
    estados = {fila["leccion_id"]: fila["estado"] for fila in conexion.execute("SELECT leccion_id, estado FROM progreso WHERE estudiante_id=?", (estudiante["id"],)).fetchall()}
    return render_template("page.html", vista="progreso", avance=progreso_curso(estudiante["id"]), lecciones=obtener_lecciones(), estados=estados)


@app.route("/resultados")
@login_requerido("estudiante")
def mis_resultados():
    conexion = obtener_db()
    estudiante = conexion.execute("SELECT id FROM estudiantes WHERE usuario_id=?", (session["usuario"]["id"],)).fetchone()
    resultados = conexion.execute("SELECT r.*, l.titulo FROM resultados r JOIN lecciones l ON l.id=r.leccion_id WHERE r.estudiante_id=? ORDER BY r.fecha DESC", (estudiante["id"],)).fetchall()
    return render_template("page.html", vista="resultados", resultados=resultados)


@app.route("/docente", methods=["GET", "POST"])
@login_requerido("docente")
def panel_docente():
    conexion = obtener_db()
    if request.method == "POST":
        if not csrf_valido():
            abort(400)
        accion = request.form.get("accion", "")
        try:
            if accion == "guardar_leccion":
                titulo = request.form.get("titulo", "").strip()
                descripcion = request.form.get("descripcion", "").strip()
                contenido = request.form.get("contenido", "").strip()
                imagen = request.form.get("imagen", "▣").strip() or "▣"
                orden = entero_formulario("orden", 1, 999)
                estado = request.form.get("estado", "publicada")
                id_leccion = entero_formulario("id", 1, 2**31 - 1) if request.form.get("id") else None
                if (
                    not texto_valido(titulo, 180)
                    or not texto_valido(descripcion, 500)
                    or not texto_valido(contenido, 20000, multilinea=True)
                    or not texto_valido(imagen, 20)
                    or orden is None
                    or estado not in {"publicada", "borrador"}
                    or (request.form.get("id") and id_leccion is None)
                ):
                    flash("Revisa los campos de la lección; el título, descripción y contenido son obligatorios y el orden debe estar entre 1 y 999.", "error")
                elif id_leccion:
                    cursor = conexion.execute("UPDATE lecciones SET titulo=?, descripcion=?, contenido=?, imagen=?, orden=?, estado=? WHERE id=?", (titulo, descripcion, contenido, imagen, orden, estado, id_leccion))
                    if cursor.rowcount == 0:
                        flash("No encontramos la lección que intentas editar.", "error")
                    else:
                        flash("Lección actualizada.", "exito")
                else:
                    conexion.execute("INSERT INTO lecciones (titulo, descripcion, contenido, imagen, orden, estado) VALUES (?, ?, ?, ?, ?, ?)", (titulo, descripcion, contenido, imagen, orden, estado))
                    flash("Lección creada.", "exito")
            elif accion == "eliminar_leccion":
                id_leccion = entero_formulario("id", 1, 2**31 - 1)
                cursor = conexion.execute("DELETE FROM lecciones WHERE id=?", (id_leccion,)) if id_leccion else None
                flash("Lección eliminada." if cursor and cursor.rowcount else "No encontramos la lección que intentas eliminar.", "exito" if cursor and cursor.rowcount else "error")
            elif accion == "guardar_pregunta":
                correcta = request.form.get("respuesta_correcta", "")
                leccion_id = entero_formulario("leccion_id", 1, 2**31 - 1)
                enunciado = request.form.get("enunciado", "").strip()
                opciones = [request.form.get(f"opcion_{letra}", "").strip() for letra in "abcd"]
                explicacion = request.form.get("explicacion", "").strip()
                id_pregunta = entero_formulario("id", 1, 2**31 - 1) if request.form.get("id") else None
                campos_validos = (
                    leccion_id is not None
                    and texto_valido(enunciado, 2000, multilinea=True)
                    and all(texto_valido(opcion, 500) for opcion in opciones)
                    and correcta in {"a", "b", "c", "d"}
                    and texto_valido(explicacion, 700, multilinea=True)
                    and (not request.form.get("id") or id_pregunta is not None)
                    and conexion.execute("SELECT 1 FROM lecciones WHERE id=?", (leccion_id,)).fetchone()
                )
                datos = (leccion_id, enunciado, *opciones, correcta, explicacion)
                if not campos_validos:
                    flash("Completa los campos de la pregunta y verifica que la lección seleccionada exista.", "error")
                elif id_pregunta:
                    cursor = conexion.execute("UPDATE preguntas SET leccion_id=?, enunciado=?, opcion_a=?, opcion_b=?, opcion_c=?, opcion_d=?, respuesta_correcta=?, explicacion=? WHERE id=?", (*datos, id_pregunta))
                    flash("Pregunta actualizada." if cursor.rowcount else "No encontramos la pregunta que intentas editar.", "exito" if cursor.rowcount else "error")
                else:
                    conexion.execute("INSERT INTO preguntas (leccion_id, enunciado, opcion_a, opcion_b, opcion_c, opcion_d, respuesta_correcta, explicacion) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", datos)
                    flash("Pregunta creada.", "exito")
            elif accion == "eliminar_pregunta":
                id_pregunta = entero_formulario("id", 1, 2**31 - 1)
                cursor = conexion.execute("DELETE FROM preguntas WHERE id=?", (id_pregunta,)) if id_pregunta else None
                flash("Pregunta eliminada." if cursor and cursor.rowcount else "No encontramos la pregunta que intentas eliminar.", "exito" if cursor and cursor.rowcount else "error")
            conexion.commit()
        except (sqlite3.IntegrityError, ValueError):
            conexion.rollback()
            flash("No se pudo guardar. Revisa los datos e inténtalo de nuevo.", "error")
        return redirect(url_for("panel_docente"))

    estudiantes = conexion.execute("""
        SELECT u.id, u.nombre, u.apellido, u.correo, e.carrera, e.trayecto,
        (SELECT COUNT(*) FROM progreso p WHERE p.estudiante_id=e.id AND p.estado='completada') AS completadas,
        (SELECT ROUND(AVG(1.0*r.puntaje/r.total_preguntas*100)) FROM resultados r WHERE r.estudiante_id=e.id) AS promedio
        FROM usuarios u JOIN estudiantes e ON e.usuario_id=u.id ORDER BY u.apellido, u.nombre
    """).fetchall()
    edit_lesson = conexion.execute("SELECT * FROM lecciones WHERE id=?", (request.args.get("editar_leccion", type=int),)).fetchone() if request.args.get("editar_leccion") else None
    edit_question = conexion.execute("SELECT * FROM preguntas WHERE id=?", (request.args.get("editar_pregunta", type=int),)).fetchone() if request.args.get("editar_pregunta") else None
    preguntas = conexion.execute("SELECT p.*, l.titulo AS leccion_titulo FROM preguntas p JOIN lecciones l ON l.id=p.leccion_id ORDER BY l.orden, p.id").fetchall()
    return render_template("page.html", vista="docente", estudiantes=estudiantes, lecciones=obtener_lecciones(False), preguntas_admin=preguntas, edit_lesson=edit_lesson, edit_question=edit_question)


@app.route("/detalle-estudiante/<int:user_id>")
@login_requerido("docente")
def detalle_estudiante(user_id: int):
    conexion = obtener_db()
    estudiante = conexion.execute("SELECT id, nombre, apellido FROM usuarios WHERE id=? AND rol='estudiante'", (user_id,)).fetchone()
    resultados = conexion.execute("SELECT r.*, l.titulo FROM resultados r JOIN lecciones l ON l.id=r.leccion_id JOIN estudiantes e ON e.id=r.estudiante_id WHERE e.usuario_id=? ORDER BY r.fecha DESC", (user_id,)).fetchall()
    return render_template("page.html", vista="detalle-estudiante", estudiante=estudiante, resultados=resultados)


@app.route("/reporte")
@login_requerido("docente")
def reporte():
    conexion = obtener_db()
    filas = conexion.execute("SELECT u.nombre, u.apellido, u.correo, l.titulo, r.puntaje, r.total_preguntas, r.fecha FROM resultados r JOIN estudiantes e ON e.id=r.estudiante_id JOIN usuarios u ON u.id=e.usuario_id JOIN lecciones l ON l.id=r.leccion_id ORDER BY u.apellido, r.fecha DESC").fetchall()
    salida = io.StringIO(newline="")
    salida.write("\ufeff")
    escritor = csv.writer(salida)
    escritor.writerow(["Estudiante", "Correo", "Lección", "Puntaje", "Total", "Porcentaje", "Fecha"])
    for fila in filas:
        escritor.writerow([f"{fila['apellido']}, {fila['nombre']}", fila["correo"], fila["titulo"], fila["puntaje"], fila["total_preguntas"], f"{round(fila['puntaje'] * 100 / fila['total_preguntas'])}%", fila["fecha"]])
    respuesta = make_response(salida.getvalue())
    respuesta.headers["Content-Type"] = "text/csv; charset=utf-8"
    respuesta.headers["Content-Disposition"] = "attachment; filename=reporte-aprendizaje.csv"
    return respuesta


@app.errorhandler(400)
def error_solicitud(error):
    return render_template("page.html", vista="error", mensaje=getattr(error, "description", "Solicitud no válida.")), 400


@app.errorhandler(404)
def pagina_no_encontrada(_error):
    return render_template("page.html", vista="error", mensaje="No encontramos esa página."), 404


inicializar_db()

if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG") == "1", port=int(os.environ.get("PORT", "5000")))