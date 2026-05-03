from pydantic import BaseModel, EmailStr

from app.schemas.user import MeResponse


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    me: MeResponse
