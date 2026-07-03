from fastapi import FastAPI
# Como main.py ahora está en la raíz, busca directamente la carpeta api
from api.models.item import Item  

app = FastAPI()

fake_items_db = [
    {"item_name": "Foo"}, {"item_name": "Bar"}, {"item_name": "Baz"},
    {"item_name": "Qux"}, {"item_name": "Quux"}, {"item_name": "Corge"},
    {"item_name": "Grault"}, {"item_name": "Garply"}, {"item_name": "Waldo"},
    {"item_name": "Fred"}, {"item_name": "Plugh"}, {"item_name": "Xyzzy"}, {"item_name": "Thud"}
]

def mimensaje():
    return "¡Hola, FastAPI!"

# 1. Raíz
@app.get("/")
def root():
    return {"message": mimensaje()}

# 2. Obtener por ID (Parámetro de Ruta)
@app.get("/items/{item_id}")
def read_item(item_id: int):
    return {"item_id": item_id}

# 3. Listar con paginación (Parámetros de Consulta)
@app.get("/items/")
def read_items(skip: int = 0, limit: int = 10, q: str | None = None):
    results = fake_items_db[skip : skip + limit]
    if q:
        results.append({"item_name": q})
    return results

# 4. Crear Item (Cuerpo de la solicitud - Body)
@app.post("/items/")
def create_item(item: Item):
    item_dict = item.model_dump()
    if item_dict is not None:
        fake_items_db.append(item_dict)
    return item_dict

# 5. Actualizar Item (Ruta + Cuerpo)
@app.put("/items/{item_name}")
def update_item(item_name: str, item: Item):
    for i, fake_item in enumerate(fake_items_db):
        if fake_item["item_name"] == item_name:
            fake_items_db[i] = item.model_dump()
            return {"item_name": item_name, **item.model_dump()}
    return {"error": "Item not found"}

# 6. Actualizar con Query (Ruta + Cuerpo + Consulta)
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