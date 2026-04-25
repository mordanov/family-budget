from fastapi import APIRouter, Depends, Form
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.user import Token, UserCreate, UserResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginForm:
    def __init__(
        self,
        username: str = Form(...),
        password: str = Form(...),
        remember_me: bool = Form(False),
    ):
        self.username = username
        self.password = password
        self.remember_me = remember_me


@router.post("/login", response_model=Token)
async def login(
    form_data: LoginForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    service = AuthService(db)
    return await service.login(form_data.username, form_data.password, form_data.remember_me)


@router.post("/register", response_model=UserResponse, status_code=201)
async def register(data: UserCreate, db: AsyncSession = Depends(get_db)):
    service = AuthService(db)
    return await service.register(data)
