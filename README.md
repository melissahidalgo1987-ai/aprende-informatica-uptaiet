# Aprende Informática UPTAIET

Aplicación educativa responsive para estudiantes de UPTAIET Rubio. Incluye cuentas de estudiante y docente, siete lecciones, cuestionarios interactivos, seguimiento del progreso y un panel de gestión. Puedes ejecutarla con Flask y SQLite sin instalar un servidor de base de datos, o con PHP y MySQL mediante XAMPP.

## Estructura

```text
aplicacionwebjohana/
├── assets/
│   ├── app.js
│   └── estilos.css
├── templates/
│   ├── base.html
│   └── page.html
├── app.py
├── config.php
├── database.sql
├── funciones.php
├── index.php
├── requirements.txt
└── README.md
└── test_app.py
```

## Inicio rápido con Flask y SQLite

1. Abre una terminal en la carpeta del proyecto.
2. Crea y activa un entorno virtual:

   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

3. Instala Flask e inicia el servidor:

   ```powershell
   pip install -r requirements.txt
   py app.py
   ```

4. Abre `http://127.0.0.1:5000`. En el primer inicio se crea `instance/aprende_informatica.sqlite3` con las tablas, siete lecciones y 35 preguntas.

El docente de prueba es `docente@uptaiet.edu.ve`, contraseña `Docente2026!`. Cambia o elimina esa cuenta antes de publicar el sitio.

## Publicar gratis en Render

Render ofrece un nivel gratuito para aplicaciones web, con una URL `onrender.com` y HTTPS. En el plan gratuito el servicio se suspende después de inactividad y su sistema de archivos es temporal: la base SQLite y los registros pueden desaparecer al suspender, reiniciar o volver a desplegar. Úsalo como demo, no como almacenamiento permanente. El manifiesto `render.yaml` configura Gunicorn, una clave de sesión generada y cookies HTTPS.

1. Crea un repositorio **público** en GitHub con el código de este proyecto, sin subir `instance/aprende_informatica.sqlite3`, `.venv` ni secretos. El `.gitignore` ya excluye la base y los archivos temporales.
2. En Render crea un **Blueprint** y conecta ese repositorio; Render detectará `render.yaml` y propondrá un servicio Free.
3. Después del despliegue, Render mostrará la URL pública. El servicio crea las lecciones automáticamente, pero no crea una cuenta docente con una contraseña pública conocida. Para habilitar al docente, define `INITIAL_TEACHER_PASSWORD` en **Environment** en Render con una contraseña privada de 8 a 72 bytes y reinicia el servicio. Luego inicia sesión con `docente@uptaiet.edu.ve` y esa contraseña. No pongas la contraseña en GitHub ni en `render.yaml`.
4. No guardes información real de estudiantes en el plan gratuito: SQLite es temporal. Para conservar datos se necesita una base de datos persistente y una migración a PostgreSQL.

## Publicar gratis en PythonAnywhere

La versión Flask/SQLite se puede alojar en el plan gratuito Beginner de [PythonAnywhere](https://www.pythonanywhere.com/). Incluye una aplicación web con subdominio `tuusuario.pythonanywhere.com` y HTTPS. El plan tiene límites de CPU y acceso saliente a internet, por lo que es adecuado para una demostración o proyecto pequeño, no para producción con tráfico importante. La base SQLite queda en el almacenamiento de tu cuenta.

1. Crea una cuenta Beginner en PythonAnywhere.
2. Descarga el [paquete para PythonAnywhere](./aplicacionwebjohana-pythonanywhere.zip) y súbelo con **Files** a `/home/tuusuario`. En una consola Bash extráelo en la carpeta del proyecto. El paquete omite la base de datos local para que no publiques registros ni la contraseña de prueba.

   ```bash
   mkdir -p /home/tuusuario/aplicacionwebjohana
   unzip /home/tuusuario/aplicacionwebjohana-pythonanywhere.zip -d /home/tuusuario/aplicacionwebjohana
   ```

3. En esa consola crea el entorno e instala Flask:

   ```bash
   mkvirtualenv --python=/usr/bin/python3.13 aprende-web
   pip install -r /home/tuusuario/aplicacionwebjohana/requirements.txt
   ```

4. En **Web**, crea una aplicación con **Manual configuration**, selecciona Python 3.13 y asigna el entorno virtual `aprende-web`.
5. Abre el archivo WSGI que aparece en la pestaña **Web** y reemplaza la sección de Flask por lo siguiente. Cambia `tuusuario` por tu nombre de usuario. Genera dos valores privados en la consola con `python -c "import secrets; print(secrets.token_hex(32))"` y colócalos en las variables indicadas; no los publiques ni los guardes en el repositorio.

   ```python
   import os
   import sys

   project_home = "/home/tuusuario/aplicacionwebjohana"
   if project_home not in sys.path:
       sys.path.insert(0, project_home)

   os.environ["FLASK_SECRET_KEY"] = "PEGA_AQUI_UN_SECRETO_ALEATORIO"
   os.environ["INITIAL_TEACHER_PASSWORD"] = "PEGA_AQUI_OTRA_CLAVE_PRIVADA"
   os.environ["FLASK_HTTPS_ONLY"] = "1"

   from app import app as application
   ```

6. Pulsa **Reload** en la pestaña **Web** y visita `https://tuusuario.pythonanywhere.com`.
7. El docente inicial es `docente@uptaiet.edu.ve`; su contraseña es el valor privado de `INITIAL_TEACHER_PASSWORD`. Al iniciar con `FLASK_SECRET_KEY`, la app no crea la cuenta docente con la contraseña de prueba publicada. No subas la base local existente: podría contener esa contraseña de prueba.

En PythonAnywhere el servidor WSGI importa `app.py`; no ejecutes `py app.py` en la consola para publicar el sitio. Conserva una copia de seguridad descargada de `instance/aprende_informatica.sqlite3` si necesitas respaldar los registros.

## Alternativa con PHP y XAMPP

1. Inicia Apache y MySQL desde el panel de XAMPP.
2. Copia la carpeta del proyecto en `C:\xampp\htdocs\aplicacionwebjohana`.
3. Abre `http://localhost/phpmyadmin` e importa `database.sql`. El script crea `aprende_informatica`, sus tablas y datos de ejemplo.
4. Comprueba en `config.php` las credenciales MySQL; el valor inicial es `root` sin contraseña.
5. Visita `http://localhost/aplicacionwebjohana/` y usa la misma cuenta docente de prueba indicada arriba.

Si ya habías creado las tablas con una versión anterior, renombra la columna de los estudiantes en phpMyAdmin antes de volver a iniciar:

```sql
ALTER TABLE estudiantes CHANGE semestre trayecto VARCHAR(30) NOT NULL DEFAULT '';
```

No uses `php -S` con un PHP que no tenga `pdo_mysql`: ese fue el origen del mensaje «could not find driver». Para evitar esa dependencia, ejecuta la alternativa Flask/SQLite.

## Uso

- El estudiante crea una cuenta, abre una lección y responde cinco preguntas, una por pantalla. Recibe retroalimentación inmediata y el resultado queda guardado.
- «Mi progreso» presenta las lecciones completadas. «Resultados» conserva cada intento, así que repetir un cuestionario no borra el puntaje anterior.
- El docente consulta el avance y promedio por estudiante, abre los puntajes por módulo, descarga un CSV y crea, edita o elimina lecciones y preguntas.
- La recuperación de contraseña funciona en modo local: genera un enlace de un solo uso que se muestra después de solicitarlo. Para un servidor público, conecta esa acción a un servicio de correo y no muestres el enlace en pantalla.

## Comprobaciones básicas

- Las contraseñas se almacenan con hash; las consultas usan parámetros preparados.
- Los formularios validan campos en navegador y servidor: correo con formato válido, longitudes máximas acordes con la base de datos, trayecto permitido y contraseña de 8 a 72 bytes. Las acciones POST verifican un token CSRF.
- Ejecuta `py -m unittest test_app.py` para probar el recorrido de estudiante y docente.
- En producción elimina la cuenta docente de prueba, usa HTTPS y define `FLASK_SECRET_KEY` como variable de entorno.
- Usa HTTPS, contraseñas individuales, copias de seguridad y credenciales MySQL distintas de `root` al desplegar.

## Accesibilidad y apoyo al aprendizaje

- Mantén instrucciones breves y una pregunta visible a la vez. La interfaz usa controles grandes, contraste legible, encabezados consistentes y anuncios accesibles para la retroalimentación.
- Se respeta `prefers-reduced-motion`; se puede navegar con teclado y los controles muestran foco visible.
- Ofrece pausas, evita temporizadores y sonidos obligatorios, y presenta ejemplos relacionados con el contexto estudiantil.
- Prueba el sitio con lectores de pantalla, zoom al 200 %, navegación solo con teclado y estudiantes de la sede. Ajusta contraste y tamaño de texto según sus comentarios.

## Notas técnicas

Flask requiere Python 3.10 o posterior. En Windows usa el lanzador `py`. La variante PHP requiere PHP 8.1 o posterior, PDO MySQL y MySQL/MariaDB; sus credenciales se cambian en `config.php`.