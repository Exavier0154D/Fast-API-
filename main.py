import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, status
from supabase import Client, create_client

from api.models.task import Task

# ==========================
# Cargar archivo .env
# ==========================

BASE_DIR = Path(__file__).resolve().parent
# Apuntamos explícitamente a la subcarpeta 'api/models' donde está guardado el archivo .env
ruta_real_env = BASE_DIR / "api" / "models" / ".env"
load_dotenv(dotenv_path=ruta_real_env)

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_PUBLISHABLE_KEY")

if url is None or key is None:
    raise RuntimeError(
        "No se encontraron las variables SUPABASE_URL o SUPABASE_PUBLISHABLE_KEY en el archivo .env"
    )

supabase: Client = create_client(url, key)

app = FastAPI(
    title="API REST con FastAPI y Supabase",
    version="1.0.0"
)


@app.get("/")
def root():
    return {
        "message": "API funcionando correctamente"
    }


# ==========================
# Obtener todas las tareas
# ==========================

@app.get("/tasks/")
def get_tasks():
    response = (
        supabase
        .table("task")
        .select("*")
        .execute()
    )

    return response.data


# ==========================
# Obtener una tarea
# ==========================

@app.get("/tasks/{task_id}")
def get_task(task_id: int):

    response = (
        supabase
        .table("task")
        .select("*")
        .eq("id", task_id)
        .execute()
    )

    if not response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task no encontrada"
        )

    return response.data[0]


# ==========================
# Crear tarea
# ==========================

@app.post("/tasks/", status_code=status.HTTP_201_CREATED)
def create_task(task: Task):

    response = (
        supabase
        .table("task")
        .insert({
            "title": task.title,
            "description": task.description
        })
        .execute()
    )

    return response.data


# ==========================
# Actualizar tarea
# ==========================

@app.put("/tasks/{task_id}")
def update_task(task_id: int, task: Task):

    response = (
        supabase
        .table("task")
        .update({
            "title": task.title,
            "description": task.description
        })
        .eq("id", task_id)
        .execute()
    )

    if not response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task no encontrada"
        )

    return response.data


# ==========================
# Eliminar tarea
# ==========================

@app.delete("/tasks/{task_id}")
def delete_task(task_id: int):

    response = (
        supabase
        .table("task")
        .delete()
        .eq("id", task_id)
        .execute()
    )

    if not response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task no encontrada"
        )

    return {
        "message": "Task eliminada correctamente"
    }