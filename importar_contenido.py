"""Carga en una instalación nueva el contenido del curso que usa la plataforma.

Al arrancar, app.py siembra el curso original: 5 temas y 24 ejercicios (seed_topics y seed_exercises). El curso de
2026 —los 12 temas de primer y tercer semestre y sus 62 ejercicios de leer, escribir y diagrama— vive en la base de
datos, porque el docente crea y corrige los ejercicios desde su panel. datos/contenido_curso.json es una copia de esas
dos tablas (temas y ejercicios, sin ningún dato de estudiantes).

Uso, con el .env de la instalación ya configurado y desde la carpeta del proyecto:

    venv/bin/python importar_contenido.py                 # usa datos/contenido_curso.json
    venv/bin/python importar_contenido.py otro_archivo.json

Solo sirve para una base sin entregas: reemplaza los temas y ejercicios de la semilla por los del archivo y conserva
sus id, porque las lecciones de lecciones.py se buscan por el id del tema.
"""
import json
import sys
from datetime import datetime

from app import app
from models import Exercise, Submission, Topic, db

ruta = sys.argv[1] if len(sys.argv) > 1 else "datos/contenido_curso.json"
with open(ruta, encoding="utf-8") as f:
    datos = json.load(f)

with app.app_context():
    if Submission.query.count():
        sys.exit("La base ya tiene entregas de estudiantes: este script es solo para una instalación nueva.")
    Exercise.query.delete()
    Topic.query.delete()
    db.session.commit()
    for tema in datos["temas"]:
        db.session.add(Topic(**tema))
    db.session.flush()
    for ejercicio in datos["ejercicios"]:
        ejercicio = dict(ejercicio)
        if ejercicio.get("created_at"):
            ejercicio["created_at"] = datetime.fromisoformat(ejercicio["created_at"])
        db.session.add(Exercise(**ejercicio))
    db.session.commit()
    print(f"Contenido cargado: {Topic.query.count()} temas y {Exercise.query.count()} ejercicios.")
