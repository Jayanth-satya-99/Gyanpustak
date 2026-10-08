from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    user_id: int
    password: str = Field(min_length=1)
    designation: str = Field(min_length=1)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str


class CurrentUserResponse(BaseModel):
    user_id: int
    designation: str