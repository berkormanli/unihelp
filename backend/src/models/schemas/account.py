import datetime

from typing import Optional

import pydantic
from pydantic import EmailStr

from src.models.schemas.base import BaseSchemaModel

class VerificationCodeModel(BaseSchemaModel):
    code: str

class AccountInCreate(BaseSchemaModel):
    username: str
    email: EmailStr
    password: str


class AccountInUpdate(BaseSchemaModel):
    username: str | None = None
    email: EmailStr | None = None
    password: str | None = None
    avatar: str | None = None


class AccountInLogin(BaseSchemaModel):
    #username: str
    email: EmailStr
    password: str

class AccountInSwaggerAuth(BaseSchemaModel):
    username: str
    password: str

class AccountWithToken(BaseSchemaModel):
    token: str
    username: str
    email: EmailStr
    avatar: str | None = None
    is_verified: bool = False
    is_active: bool
    is_logged_in: bool
    created_at: datetime.datetime
    updated_at: datetime.datetime | None


class AccountInResponse(BaseSchemaModel):
    id: int
    authorized_account: AccountWithToken

class AccountDetailBase(BaseSchemaModel):
    avatar: Optional[str]
    username: str
    full_name: str