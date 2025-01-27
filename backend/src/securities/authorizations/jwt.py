import datetime

import pydantic
from jose import jwt as jose_jwt, JWTError as JoseJWTError

from src.config.manager import settings
from src.models.db.account import Account
from src.models.schemas.jwt import JWTAccount, JWTVerification, JWToken
from src.utilities.exceptions.database import EntityDoesNotExist


class JWTGenerator:
    def __init__(self):
        pass

    def _generate_jwt_token(
        self,
        *,
        jwt_data: dict[str, str],
        expires_delta: datetime.timedelta | None = None,
    ) -> str:
        to_encode = jwt_data.copy()

        if expires_delta:
            expire = datetime.datetime.utcnow() + expires_delta

        else:
            expire = datetime.datetime.utcnow() + datetime.timedelta(minutes=settings.JWT_MIN)

        to_encode.update(JWToken(exp=expire, sub=settings.JWT_SUBJECT).dict())

        return jose_jwt.encode(to_encode, key=settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

    def generate_access_token(self, account: Account) -> str:
        if not account:
            raise EntityDoesNotExist(f"Cannot generate JWT token for without Account entity!")

        return self._generate_jwt_token(
            jwt_data=JWTAccount(username=account.username, email=account.email).dict(),  # type: ignore
            expires_delta=datetime.timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRATION_TIME),
        )

    def generate_verification_token(self, account_id: int) -> str:
        """Generates a JWT token for email verification."""
        return self._generate_jwt_token(
            jwt_data=JWTVerification(account_id=account_id).dict(),
            expires_delta=datetime.timedelta(hours=settings.JWT_VERIFICATION_TOKEN_LIFETIME),  # Shorter expiration
        )

    def retrieve_details_from_token(self, token: str, secret_key: str) -> list[str]:
        try:
            payload = jose_jwt.decode(token=token, key=secret_key, algorithms=[settings.JWT_ALGORITHM])
            jwt_account = JWTAccount(username=payload["username"], email=payload["email"])

        except JoseJWTError as token_decode_error:
            raise ValueError("Unable to decode JWT Token") from token_decode_error

        except pydantic.ValidationError as validation_error:
            raise ValueError("Invalid payload in token") from validation_error

        return [jwt_account.username, jwt_account.email]

    def verify_verification_token(self, token: str) -> int:
        """Verifies a verification token and returns the account ID."""
        try:
            payload = jose_jwt.decode(
                token=token,
                key=settings.JWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM],
                options={"verify_exp": True},  # Ensure expiration is checked
            )

            if "account_id" not in payload:
                raise Exception("Invalid Account ID!")

            return payload["account_id"]

        except JoseJWTError:
                raise Exception("Invalid Token!")
        except pydantic.ValidationError:
                raise Exception("Invalid Token!")

    def retrieve_details_from_token(self, token: str, secret_key: str) -> list[str]:
        try:
            payload = jose_jwt.decode(token=token, key=secret_key, algorithms=[settings.JWT_ALGORITHM])
            jwt_account = JWTAccount(username=payload["username"], email=payload["email"])

        except JoseJWTError as token_decode_error:
            raise ValueError("Unable to decode JWT Token") from token_decode_error

        except pydantic.ValidationError as validation_error:
            raise ValueError("Invalid payload in token") from validation_error

        return [jwt_account.username, jwt_account.email]

    def verify_token(self, token: str) -> dict:
        """Verifies and decodes a JWT token."""
        try:
            payload = jose_jwt.decode(
                token=token,
                key=settings.JWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM],
                options={"verify_exp": True}
            )
            return payload
        except JoseJWTError:
            raise ValueError("Invalid token")
        except pydantic.ValidationError:
            raise ValueError("Invalid payload in token")

def get_jwt_generator() -> JWTGenerator:
    return JWTGenerator()


jwt_generator: JWTGenerator = get_jwt_generator()
