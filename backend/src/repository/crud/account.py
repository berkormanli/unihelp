import random
import string
import typing

import sqlalchemy
from sqlalchemy.sql import functions as sqlalchemy_functions

from src.models.db.account import Account
from src.models.schemas.account import AccountInCreate, AccountInLogin, AccountInUpdate, AccountInSwaggerAuth
from src.repository.crud.base import BaseCRUDRepository
from src.securities.hashing.password import pwd_generator
from src.securities.verifications.credentials import credential_verifier
from src.utilities.exceptions.database import EntityAlreadyExists, EntityDoesNotExist
from src.utilities.exceptions.password import PasswordDoesNotMatch
from src.utilities.services.mail_service import MailService
from src.securities.authorizations.jwt import get_jwt_generator

jwt_generator = get_jwt_generator()

# Gmail uygulama şifresi (dou.unihelp@gmail.com için)
# xxfv bvmo rywe glpl

mail_service = MailService({
    "host": "smtp.gmail.com",
    "port": 587,
    "username": "dou.unihelp",
    "password": "xxfv bvmo rywe glpl",
    "from": "dou.unihelp"
})

class AccountCRUDRepository(BaseCRUDRepository):
    """
    Hesap CRUD işlemleri için repository sınıfı.
    """
    async def create_account(self, account_create: AccountInCreate) -> Account:
        """
        Yeni bir hesap oluşturur.

        Args:
            account_create (AccountInCreate): Hesap oluşturma şeması.

        Returns:
            Account: Oluşturulan hesap modeli.
        """
        verification_code = ''.join(random.choices(string.digits, k=6)) # 6 haneli doğrulama kodu oluşturur
        new_account = Account(
            username=account_create.username,
            email=account_create.email,
            is_logged_in=True,
            verification_code=verification_code,
            is_verified=False
        )

        new_account.set_hash_salt(hash_salt=pwd_generator.generate_salt) # Hash tuzu ayarlar
        new_account.set_hashed_password(
            hashed_password=pwd_generator.generate_hashed_password(
                hash_salt=new_account.hash_salt, new_password=account_create.password
            )
        ) # Şifreyi hashleyerek ayarlar

        self.async_session.add(instance=new_account) # Yeni hesabı oturuma ekler
        await self.async_session.commit() # Veritabanına kaydeder
        await self.async_session.refresh(instance=new_account) # Hesabı yeniler

        # Doğrulama linki oluştur
        verification_token = jwt_generator.generate_verification_token(account_id=new_account.id)
        #base_url = "http://your-app-url.com"  # Uygulamanızın URL'si ile değiştirin
        verification_url = f"/auth/verify/{verification_token}"

        # Doğrulama e-postası gönder
        mail_service.send_verification_code(
            to=[new_account.email],
            code=verification_code,
            verification_url=verification_url  # Şimdilik kod doğrulaması kullanacağız
        )

        return new_account

    async def read_accounts(self) -> typing.Sequence[Account]:
        """
        Tüm hesapları okur.

        Returns:
            typing.Sequence[Account]: Hesap modelleri listesi.
        """
        stmt = sqlalchemy.select(Account)
        query = await self.async_session.execute(statement=stmt)
        return query.scalars().all()

    async def read_account_by_id(self, id: int) -> Account:
        """
        ID'ye göre hesabı okur.

        Args:
            id (int): Hesap ID'si.

        Returns:
            Account: Hesap modeli.

        Raises:
            EntityDoesNotExist: Hesap bulunamazsa.
        """
        stmt = sqlalchemy.select(Account).where(Account.id == id)
        query = await self.async_session.execute(statement=stmt)

        if not query:
            raise EntityDoesNotExist(f"Account with id `{id}` does not exist!")

        return query.scalar()  # type: ignore

    async def read_account_by_username(self, username: str) -> Account:
        """
        Kullanıcı adına göre hesabı okur.

        Args:
            username (str): Kullanıcı adı.

        Returns:
            Account: Hesap modeli.

        Raises:
            EntityDoesNotExist: Hesap bulunamazsa.
        """
        stmt = sqlalchemy.select(Account).where(Account.username == username)
        query = await self.async_session.execute(statement=stmt)

        if not query:
            raise EntityDoesNotExist(f"Account with username `{username}` does not exist!")

        return query.scalar()  # type: ignore

    async def read_account_by_email(self, email: str) -> Account:
        """
        E-posta adresine göre hesabı okur.

        Args:
            email (str): E-posta adresi.

        Returns:
            Account: Hesap modeli.

        Raises:
            EntityDoesNotExist: Hesap bulunamazsa.
        """
        stmt = sqlalchemy.select(Account).where(Account.email == email)
        query = await self.async_session.execute(statement=stmt)

        if not query:
            raise EntityDoesNotExist(f"Account with email `{email}` does not exist!")

        return query.scalar()  # type: ignore

    async def read_user_by_password_authentication(self, account_login: AccountInLogin) -> Account:
        """
        E-posta ve şifre ile kullanıcıyı doğrular.

        Args:
            account_login (AccountInLogin): Giriş şeması.

        Returns:
            Account: Hesap modeli.

        Raises:
            EntityDoesNotExist: E-posta adresi yanlışsa.
            PasswordDoesNotMatch: Şifre yanlışsa.
        """
        stmt = sqlalchemy.select(Account).where(
            Account.email == account_login.email
        )
        query = await self.async_session.execute(statement=stmt)
        db_account = query.scalar()

        if not db_account:
            raise EntityDoesNotExist("Wrong email!")

        if not pwd_generator.is_password_authenticated(hash_salt=db_account.hash_salt, password=account_login.password, hashed_password=db_account.hashed_password):  # type: ignore
            raise PasswordDoesNotMatch("Password does not match!")

        return db_account  # type: ignore

    async def read_user_by_password_authentication_swagger(self, account_login: AccountInSwaggerAuth) -> Account:
        """
        Kullanıcı adı ve şifre ile kullanıcıyı doğrular (Swagger için).

        Args:
            account_login (AccountInSwaggerAuth): Swagger giriş şeması.

        Returns:
            Account: Hesap modeli.

        Raises:
            EntityDoesNotExist: Kullanıcı adı yanlışsa.
            PasswordDoesNotMatch: Şifre yanlışsa.
        """
        stmt = sqlalchemy.select(Account).where(
            Account.username == account_login.username
        )
        query = await self.async_session.execute(statement=stmt)
        db_account = query.scalar()

        if not db_account:
            raise EntityDoesNotExist("Wrong username!")

        if not pwd_generator.is_password_authenticated(hash_salt=db_account.hash_salt, password=account_login.password, hashed_password=db_account.hashed_password):  # type: ignore
            raise PasswordDoesNotMatch("Password does not match!")

        return db_account  # type: ignore

    async def update_account_by_id(self, id: int, account_update: AccountInUpdate) -> Account:
        """
        ID'ye göre hesabı günceller.

        Args:
            id (int): Hesap ID'si.
            account_update (AccountInUpdate): Hesap güncelleme şeması.

        Returns:
            Account: Güncellenmiş hesap modeli.

        Raises:
            EntityDoesNotExist: Hesap bulunamazsa.
        """
        new_account_data = account_update.dict()

        select_stmt = sqlalchemy.select(Account).where(Account.id == id)
        query = await self.async_session.execute(statement=select_stmt)
        update_account = query.scalar()

        if not update_account:
            raise EntityDoesNotExist(f"Account with id `{id}` does not exist!")  # type: ignore

        update_stmt = sqlalchemy.update(table=Account).where(Account.id == update_account.id).values(updated_at=sqlalchemy_functions.now())  # type: ignore

        if new_account_data["username"]:
            update_stmt = update_stmt.values(username=new_account_data["username"])

        if new_account_data["email"]:
            update_stmt = update_stmt.values(username=new_account_data["email"])

        if new_account_data["password"]:
            update_account.set_hash_salt(hash_salt=pwd_generator.generate_salt)  # type: ignore
            update_account.set_hashed_password(hashed_password=pwd_generator.generate_hashed_password(hash_salt=update_account.hash_salt, new_password=new_account_data["password"]))  # type: ignore

        await self.async_session.execute(statement=update_stmt)
        await self.async_session.commit()
        await self.async_session.refresh(instance=update_account)

        return update_account  # type: ignore

    async def delete_account_by_id(self, id: int) -> str:
        """
        ID'ye göre hesabı siler.

        Args:
            id (int): Hesap ID'si.

        Returns:
            str: Başarı mesajı.

        Raises:
            EntityDoesNotExist: Hesap bulunamazsa.
        """
        select_stmt = sqlalchemy.select(Account).where(Account.id == id)
        query = await self.async_session.execute(statement=select_stmt)
        delete_account = query.scalar()

        if not delete_account:
            raise EntityDoesNotExist(f"Account with id `{id}` does not exist!")  # type: ignore

        stmt = sqlalchemy.delete(table=Account).where(Account.id == delete_account.id)

        await self.async_session.execute(statement=stmt)
        await self.async_session.commit()

        return f"Account with id '{id}' is successfully deleted!"

    async def is_username_taken(self, username: str) -> bool:
        """
        Kullanıcı adının alınıp alınmadığını kontrol eder.

        Args:
            username (str): Kullanıcı adı.

        Returns:
            bool: Kullanıcı adı alınmışsa True, değilse False.

        Raises:
            EntityAlreadyExists: Kullanıcı adı zaten alınmışsa.
        """
        username_stmt = sqlalchemy.select(Account.username).select_from(Account).where(Account.username == username)
        username_query = await self.async_session.execute(username_stmt)
        db_username = username_query.scalar()

        if not credential_verifier.is_username_available(username=db_username):
            raise EntityAlreadyExists(f"The username `{username}` is already taken!")  # type: ignore

        return True

    async def is_email_taken(self, email: str) -> bool:
        """
        E-posta adresinin kayıtlı olup olmadığını kontrol eder.

        Args:
            email (str): E-posta adresi.

        Returns:
            bool: E-posta adresi kayıtlıysa True, değilse False.

        Raises:
            EntityAlreadyExists: E-posta adresi zaten kayıtlıysa.
        """
        email_stmt = sqlalchemy.select(Account.email).select_from(Account).where(Account.email == email)
        email_query = await self.async_session.execute(email_stmt)
        db_email = email_query.scalar()

        if not credential_verifier.is_email_available(email=db_email):
            raise EntityAlreadyExists(f"The email `{email}` is already registered!")  # type: ignore

        return True

    async def update_verification_code(self, account_id: int, code: str) -> None:
        """Doğrulama kodunu günceller."""
        account = await self.read_account_by_id(account_id)
        account.verification_code = code
        await self.async_session.commit()

    async def verify_account(self, account_id: int) -> None:
        """Hesabı doğrulanmış olarak işaretler."""
        account = await self.read_account_by_id(account_id)
        account.is_verified = True
        account.verification_code = None
        await self.async_session.commit()
