from sqlalchemy.ext.asyncio import AsyncSession as SQLAlchemyAsyncSession


class BaseCRUDRepository:
    """
    Temel CRUD (Oluştur, Oku, Güncelle, Sil) işlemleri için temel repository sınıfı.
    """
    def __init__(self, async_session: SQLAlchemyAsyncSession):
        """
        Yapıcı metot.

        Args:
            async_session (SQLAlchemyAsyncSession): SQLAlchemy asenkron oturumu.
        """
        self.async_session = async_session
