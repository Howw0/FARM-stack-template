from beanie import Document, Link, PydanticObjectId, before_event, after_event, Delete, Insert
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List

class UserBase(BaseModel):
    """
    Shared properties
    """
    email: EmailStr
    is_active: bool = True
    is_superuser: bool = False
    full_name: Optional[str] = None

class UserCreate(UserBase):
    """
    Properties to receive via API on creation
    """
    password: str = Field(min_length=8, max_length=40)


class UserRegister(BaseModel):
    """
    Registration properties
    """
    email: EmailStr = Field(max_length=255)
    password: str = Field(min_length=8, max_length=40)
    full_name: Optional[str] = Field(default=None, max_length=255)


class UserUpdate(UserBase):
    """
    Properties to receive via API on update, all are optional
    """
    email: Optional[EmailStr] = Field(default=None, max_length=255)  # type: ignore
    password: Optional[str] = Field(default=None, min_length=8, max_length=40)


class UserUpdateMe(BaseModel):
    """
    Properties for updating user details
    """
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None


class UpdatePassword(BaseModel):
    """
    Update password model
    """
    current_password: str = Field(min_length=8, max_length=40)
    new_password: str = Field(min_length=8, max_length=40)


class User(Document, UserBase):
    """
    Database model, database table inferred from class name
    """
    id: PydanticObjectId = Field(default_factory=PydanticObjectId)
    hashed_password: str
    items: List[Link["Item"]] = Field(default_factory=list)

    class Settings:
        name = "users"
        indexes = [
            "email"
        ]

    @before_event(Delete)
    async def cascade_delete(self):
        await Item.find(Item.owner_id == self.id).delete()

class UserPublic(UserBase):
    """
    Properties to return via API, id is always required
    """
    id: PydanticObjectId


class UsersPublic(BaseModel):
    """
    List of users to be returned via API
    """
    data: List[UserPublic]
    count: int


class Message(BaseModel):
    """
    Generic message model
    """
    message: str


class Token(BaseModel):
    """
    JSON payload containing access token
    """
    access_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    """
    Contents of JWT token
    """
    sub: Optional[str] = None


class NewPassword(BaseModel):
    """
    Model for setting a new password
    """
    token: str
    new_password: str = Field(min_length=8, max_length=40)


class ItemBase(BaseModel):
    """
    Shared properties for items
    """
    title: str
    description: Optional[str] = None


class ItemCreate(ItemBase):
    """
    Properties to receive on item creation
    """
    pass


class ItemUpdate(ItemBase):
    """
    Properties to receive on item update
    """
    title: Optional[str] = Field(default=None, min_length=1, max_length=255)


class Item(Document, ItemBase):
    id: PydanticObjectId = Field(default_factory=PydanticObjectId)
    owner_id: PydanticObjectId
    owner: Link[User]

    class Settings:
        name = "items"
        indexes = [
            "title",
            "owner_id"
        ]
        
    @after_event(Insert)
    async def userlink_insert(self) -> None:
        owner = await User.get(self.owner_id)
        owner.items.append(self.to_ref())
        await owner.set({"items": owner.items})

    @before_event(Delete)
    async def userlink_delete(self) -> None:
        owner = await User.get(self.owner_id)
        owner.items = [link for link in owner.items if link.ref.id != self.id]
        await owner.set({"items": owner.items})


class ItemPublic(ItemBase):
    """
    Properties to return via API, id is always required
    """
    id: PydanticObjectId
    owner_id: PydanticObjectId


class ItemsPublic(BaseModel):
    """
    List of items to be returned via API
    """
    data: List[ItemPublic]
    count: int
