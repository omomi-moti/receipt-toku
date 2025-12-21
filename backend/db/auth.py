from typing import Annotated

from config import settings
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt  # type: ignore
from loguru import logger

security = HTTPBearer()


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)]
) -> dict[str, str]:
    """
    Supabase JWTトークンを検証し、ユーザー情報を返す。
    """
    token = credentials.credentials
    jwt_secret = settings.SUPABASE_JWT_SECRET

    if not jwt_secret:
        logger.error("SUPABASE_JWT_SECRET is not set")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server configuration error: JWT secret not set",
        )

    try:
        # Supabaseのトークンを検証
        # Supabaseはデフォルトで HS256 を使用
        payload = jwt.decode(
            token,
            jwt_secret,
            algorithms=["HS256"],
            audience="authenticated",
        )
        user_id: str = payload.get("sub", "")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing sub claim",
            )

        email: str = payload.get("email", "")
        role: str = payload.get("role", "")

        return {
            "id": user_id,
            "email": email,
            "role": role,
        }
    except JWTError as e:
        logger.error(f"JWT verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}",
        )


# 依存性注入用のエイリアス
CurrentUser = Annotated[dict[str, str], Depends(get_current_user)]
