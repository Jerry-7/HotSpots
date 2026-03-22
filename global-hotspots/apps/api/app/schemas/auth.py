from pydantic import BaseModel, EmailStr


class RequestOtpIn(BaseModel):
    email: EmailStr


class VerifyOtpIn(BaseModel):
    email: EmailStr
    code: str


class AuthOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
