import os
from pathlib import Path
from typing import Annotated

from dotenv import load_dotenv
from fastapi import FastAPI, Form, HTTPException, Response, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from supabase import Client, create_client

# Importación de tus modelos
from api.models.task import Task
from api.models.item import Item
from api.models.form_data import FormData

# 1. Configuración de rutas y variables de entorno
BASE_DIR = Path(__file__).resolve().parent
# Apuntar directamente a la raíz del proyecto para leer el archivo .env
ruta_real_env = BASE_DIR / ".env"
load_dotenv(dotenv_path=ruta_real_env)

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_PUBLISHABLE_KEY")

if url is None or key is None:
    raise RuntimeError(
        "No se encontraron las variables SUPABASE_URL o SUPABASE_PUBLISHABLE_KEY en el archivo .env"
    )

# 2. Inicialización del cliente base de Supabase
supabase: Client = create_client(url, key)

app = FastAPI(
    title="API REST con FastAPI y Supabase",
    version="1.0.0"
)

security = HTTPBearer()

# 3. Dependencia para obtener el cliente de Supabase autenticado con el JWT del usuario
def get_supabase_client(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Client:
    token = credentials.credentials
    try:
        # Creamos un cliente nuevo específico para la petición
        client = create_client(url, key)
        # Seteamos el token del usuario para que se aplique el RLS en Supabase
        client.postgrest.auth(token)
        return client
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de Supabase inválido o expirado"
        )

# Base de datos simulada en memoria
fake_items_db = [
    {"item_name": "Foo"}, {"item_name": "Bar"}, {"item_name": "Baz"}, 
    {"item_name": "Qux"}, {"item_name": "Quux"}, {"item_name": "Corge"}, 
    {"item_name": "Grault"}, {"item_name": "Garply"}, {"item_name": "Waldo"}, 
    {"item_name": "Fred"}, {"item_name": "Plugh"}, {"item_name": "Xyzzy"}, 
    {"item_name": "Thud"}
]


def mimensaje():
    return "¡Hola, FastAPI!"


@app.get("/")
def root():
    return {
        "message": mimensaje()
    }


# --- ENDPOINTS DE AUTENTICACIÓN ---

@app.post("/auth/login-temporal")
def login_temporal(email: str, password: str):
    import requests
    # Endpoint nativo de Supabase Auth
    auth_url = f"{url}/auth/v1/token?grant_type=password"
    headers = {"apikey": key, "Content-Type": "application/json"}
    payload = {"email": email, "password": password}

    response = requests.post(auth_url, json=payload, headers=headers)
    if response.status_code != 200:
        raise HTTPException(status_code=400, detail="Credenciales incorrectas en Supabase")

    # Retornamos el access_token (JWT)
    return {"access_token": response.json().get("access_token")}


# --- ENDPOINTS DE ITEMS ---

@app.get("/items/{item_id}")
def read_item(item_id: int):
    return {"item_id": item_id}


@app.get("/items/")
def read_items(skip: int = 0, limit: int = 10, q: str | None = None):
    results = fake_items_db[skip : skip + limit]
    if q:
        results.append({"item_name": q})
    return results


@app.post("/items/")
def create_item(item: Item):
    item_dict = item.model_dump()
    if item_dict is not None:
        fake_items_db.append(item_dict)
    return item_dict


@app.put("/items/{item_name}")
def update_item(item_name: str, item: Item):
    for i, fake_item in enumerate(fake_items_db):
        if fake_item["item_name"] == item_name:
            fake_items_db[i] = item.model_dump()
            return {"item_name": item_name, **item.model_dump()}
    return {"error": "Item not found"}


@app.put("/items/{item_name}/query")
def update_item_with_query(item_name: str, item: Item, q: str | None = None):
    for i, fake_item in enumerate(fake_items_db):
        if fake_item["item_name"] == item_name:
            fake_items_db[i] = item.model_dump()
            response = {"item_name": item_name, **item.model_dump()}
            if q:
                response.update({"q": q})
            return response
    return {"error": "Item not found"}


@app.post("/items_form/")
def create_item_form(
    item_name: Annotated[str, Form()],
    description: Annotated[str, Form()],
    price: Annotated[float, Form()],
    tax: Annotated[float, Form()]
):
    if tax < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tax cannot be negative."
        )

    form_data = FormData(
        item_name=item_name,
        description=description,
        price=price,
        tax=tax
    )

    message_str = f"Item '{form_data.item_name}' created successfully with description '{form_data.description}', price {form_data.price}, and tax {form_data.tax}."

    fake_items_db.append({"item_name": item_name})

    return Response(content=message_str, status_code=201)


# --- ENDPOINTS DE TASKS (CON RLS / AUTENTICACIÓN) ---

@app.get("/tasks/", status_code=status.HTTP_200_OK)
def get_tasks(supabase_client: Client = Depends(get_supabase_client)):
    try:
        # Usamos el cliente autenticado que inyecta la dependencia Depends
        response = supabase_client.table("task").select("*").execute()
        return response.data
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al recuperar las tareas desde la base de datos."
        )


@app.get("/tasks/{task_id}")
def get_task(task_id: int, supabase_client: Client = Depends(get_supabase_client)):
    response = (
        supabase_client
        .table("task")
        .select("*")
        .eq("id", task_id)
        .execute()
    )

    if not response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task no encontrada o no tienes permisos de acceso."
        )

    return response.data[0]


@app.post("/tasks/", status_code=status.HTTP_201_CREATED)
def create_task(task: Task, supabase_client: Client = Depends(get_supabase_client)):
    response = (
        supabase_client
        .table("task")
        .insert({
            "title": task.title,
            "description": task.description
        })
        .execute()
    )
    return response.data


@app.put("/tasks/{task_id}")
def update_task(task_id: int, task: Task, supabase_client: Client = Depends(get_supabase_client)):
    response = (
        supabase_client
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
            detail="Task no encontrada o no tienes permisos de edición."
        )

    return response.data


@app.delete("/tasks/{task_id}")
def delete_task(task_id: int, supabase_client: Client = Depends(get_supabase_client)):
    response = (
        supabase_client
        .table("task")
        .delete()
        .eq("id", task_id)
        .execute()
    )

    if not response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task no encontrada o no tienes permisos para eliminarla."
        )

    return {
        "message": "Task eliminada correctamente"
    }