from fastapi import FastAPI
from api.models.item import Item  # Importación desde tu módulo local

app = FastAPI()

fake_items_db = [
    {"item_name": "Foo", "description": "Un item inicial", "price": 42.0, "tax": 3.2},
    {"item_name": "Bar", "description": "Otro item", "price": 15.5, "tax": None}
]

@app.get("/")
def home():
    return {"message": "¡Hola, Fast API!"}


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