from typing import Annotated

from fastapi import FastAPI, Form, Response, HTTPException, status

from api.models.item import Item
from api.models.form_data import FormData

app = FastAPI()

fake_items_db = [
    {"item_name": "Foo"},
    {"item_name": "Bar"},
    {"item_name": "Baz"},
    {"item_name": "Qux"},
    {"item_name": "Quux"},
    {"item_name": "Corge"},
    {"item_name": "Grault"},
    {"item_name": "Garply"},
    {"item_name": "Waldo"},
    {"item_name": "Fred"},
    {"item_name": "Plugh"},
    {"item_name": "Xyzzy"},
    {"item_name": "Thud"},
]


def mimensaje():
    return "¡Hola, FastAPI!"


@app.get("/")
def root():
    return {"message": mimensaje()}


@app.get("/items/{item_id}")
def read_item(item_id: int):
    return {"item_id": item_id}


@app.get("/items/")
def read_items(skip: int = 0, limit: int = 10, q: str | None = None):
    results = fake_items_db[skip: skip + limit]

    if q:
        results.append({"item_name": q})

    return results


@app.post("/items/")
def create_item(item: Item):
    item_dict = item.model_dump()
    fake_items_db.append(item_dict)
    return item_dict


@app.put("/items/{item_name}")
def update_item(item_name: str, item: Item):
    for i, fake_item in enumerate(fake_items_db):
        if fake_item["item_name"] == item_name:
            fake_items_db[i] = item.model_dump()
            return {"item_name": item_name, **item.model_dump()}

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Item not found"
    )


@app.put("/items/{item_name}/query")
def update_item_with_query(
    item_name: str,
    item: Item,
    q: str | None = None
):
    for i, fake_item in enumerate(fake_items_db):
        if fake_item["item_name"] == item_name:
            fake_items_db[i] = item.model_dump()

            response = {
                "item_name": item_name,
                **item.model_dump()
            }

            if q:
                response["q"] = q

            return response

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Item not found"
    )


@app.post("/items_form/")
def create_item_form(
    item_name: Annotated[str, Form()],
    description: Annotated[str, Form()],
    price: Annotated[float, Form()],
    tax: Annotated[float, Form()],
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
        tax=tax,
    )

    fake_items_db.append(form_data.model_dump())

    message = (
        f"Item '{form_data.item_name}' created successfully "
        f"with description '{form_data.description}', "
        f"price {form_data.price}, and tax {form_data.tax}."
    )

    return Response(
        content=message,
        status_code=status.HTTP_201_CREATED
    )