from typing import Any
from beanie import PydanticObjectId
from fastapi import APIRouter, HTTPException
from app.api.deps import CurrentUser, SessionDep
from app.models import Item, ItemCreate, ItemPublic, ItemsPublic, ItemUpdate, Message
from app.db import crud

router = APIRouter()


@router.get("/", response_model=ItemsPublic)
async def read_items(session: SessionDep, current_user: CurrentUser, skip: int = 0, limit: int = 100) -> Any:
    """
    Retrieve items.
    """
    if current_user.is_superuser:
        count = await Item.find().count()
        items = await Item.find(skip=skip, limit=limit).to_list()
    else:
        count = await Item.find(Item.owner_id == current_user.id).count()
        items = await Item.find(Item.owner_id == current_user.id, skip=skip, limit=limit).to_list()
    items_public = [ItemPublic.model_validate(item.model_dump()) for item in items]
    return ItemsPublic(data=items_public, count=count)


@router.get("/{id}", response_model=ItemPublic)
async def read_item(session: SessionDep, current_user: CurrentUser, id: PydanticObjectId) -> Any:
    """
    Get item by ID.
    """
    item = await Item.get(id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    if not current_user.is_superuser and (item.owner_id != current_user.id):
        raise HTTPException(status_code=400, detail="Not enough permissions")
    return item


@router.post("/", response_model=ItemPublic)
async def create_item(session: SessionDep, current_user: CurrentUser, item_in: ItemCreate) -> Any:
    """
    Create new item.
    """
    item = await crud.create_item(session=session, user=current_user, item_in=item_in)
    return item


@router.put("/{id}", response_model=ItemPublic)
async def update_item(session: SessionDep, current_user: CurrentUser, id: PydanticObjectId, item_in: ItemUpdate) -> Any:
    """
    Update an item.
    """
    item = await Item.get(id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    if not current_user.is_superuser and (item.owner_id != current_user.id):
        raise HTTPException(status_code=400, detail="Not enough permissions")
    await item.set(item_in.model_dump(exclude_unset=True))
    return item


@router.delete("/{id}")
async def delete_item(session: SessionDep, current_user: CurrentUser, id: PydanticObjectId) -> Message:
    """
    Delete an item.
    """
    item = await Item.get(id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    if not current_user.is_superuser and (item.owner_id != current_user.id):
        raise HTTPException(status_code=400, detail="Not enough permissions")
    await item.delete()
    return Message(message="Item deleted successfully")
