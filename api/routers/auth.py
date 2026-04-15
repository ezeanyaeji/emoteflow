from fastapi import APIRouter, HTTPException, Request, Response, status, Depends

from api.models.user import UserRegister, UserLogin, UserResponse, TokenResponse, UserUpdate
from api.services.auth import register_user, authenticate_user, create_tokens, refresh_access_token
from api.core.dependencies import get_current_user
from api.core.config import get_settings

router = APIRouter(prefix="/auth", tags=["Authentication"])

_settings = get_settings()
_REFRESH_MAX_AGE = _settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600


def _set_refresh_cookie(response: Response, refresh_token: str) -> None:
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=False,       # set True in production (HTTPS)
        samesite="lax",
        max_age=_REFRESH_MAX_AGE,
        path="/api/auth",
    )


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(data: UserRegister):
    user = await register_user(data)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )
    return UserResponse(
        id=user["id"],
        email=user["email"],
        first_name=user["first_name"],
        last_name=user["last_name"],
        role=user["role"],
        consent_camera=user.get("consent_camera", False),
        created_at=user["created_at"],
    )


@router.post("/login", response_model=TokenResponse)
async def login(data: UserLogin, response: Response):
    user = await authenticate_user(data.email, data.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    tokens = create_tokens(user["id"], user["role"])
    _set_refresh_cookie(response, tokens["refresh_token"])
    return TokenResponse(access_token=tokens["access_token"])


@router.post("/refresh", response_model=TokenResponse)
async def refresh(request: Request, response: Response):
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing refresh token",
        )
    tokens = await refresh_access_token(refresh_token)
    if tokens is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )
    _set_refresh_cookie(response, tokens["refresh_token"])
    return TokenResponse(access_token=tokens["access_token"])


@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie(
        key="refresh_token",
        httponly=True,
        secure=False,
        samesite="lax",
        path="/api/auth",
    )
    return {"detail": "Logged out"}


@router.get("/me", response_model=UserResponse)
async def get_me(user: dict = Depends(get_current_user)):
    return UserResponse(
        id=user["id"],
        email=user["email"],
        first_name=user["first_name"],
        last_name=user["last_name"],
        role=user["role"],
        consent_camera=user.get("consent_camera", False),
        created_at=user["created_at"],
    )


@router.patch("/me", response_model=UserResponse)
async def update_me(data: UserUpdate, user: dict = Depends(get_current_user)):
    from bson import ObjectId
    from api.core.database import get_db

    db = get_db()
    update_data = data.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No fields to update")

    await db.users.update_one({"_id": ObjectId(user["id"])}, {"$set": update_data})
    updated = await db.users.find_one({"_id": ObjectId(user["id"])})
    updated["id"] = str(updated["_id"])
    return UserResponse(
        id=updated["id"],
        email=updated["email"],
        first_name=updated["first_name"],
        last_name=updated["last_name"],
        role=updated["role"],
        consent_camera=updated.get("consent_camera", False),
        created_at=updated["created_at"],
    )
