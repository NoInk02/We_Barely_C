from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from Backend.support.jwt import verify_token

admin_oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/admin/login")

async def require_admin_token(token: str = Depends(admin_oauth2_scheme)) -> str:
    username = verify_token(token)
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return username
