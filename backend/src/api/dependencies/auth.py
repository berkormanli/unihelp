from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from src.models.db.account import Account
from src.repository.crud.account import AccountCRUDRepository
from src.securities.authorizations.jwt import get_jwt_generator
from .repository import get_repository

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/signinswagger", auto_error=False)
jwt_generator = get_jwt_generator()

async def get_current_user(
    token: str | None = Depends(oauth2_scheme),
    account_repo: AccountCRUDRepository = Depends(get_repository(AccountCRUDRepository))
) -> Account | None:
    if not token:
        return None
        
    try:
        payload = jwt_generator.verify_token(token)
        user_email = payload.get("email")
        if user_email is None:
            return None
    except:
        return None

    try:
        user = await account_repo.read_account_by_email(user_email)
        return user
    except:
        return None