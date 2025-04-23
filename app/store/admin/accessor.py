import logging
import typing

from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.admin.models import AdminModel
from app.web.exceptions import AdminCreateError, AdminDeleteError
from app.web.utils import hash_password

if typing.TYPE_CHECKING:
    from app.store.store import Store


logger = logging.getLogger(__name__)


class AdminAccessor:
    def __init__(self, store: "Store") -> None:
        self.store = store

    async def connect(self, *args: typing.Any, **kwargs: typing.Any) -> None:
        email = self.store.config.admin.email
        password = hash_password(self.store.config.admin.password)
        try:
            await self.create_admin(email, password)
            logger.info("Base Admin created successfully")
        except AdminCreateError:
            logger.info("Base Admin  has already been created")

    async def disconnect(self, *args: typing.Any, **kwargs: typing.Any) -> None:
        await self.delete_admin_by_email(self.store.config.admin.email)
        logger.info("Base Admin deleted successfully")

    async def get_by_email(self, email: str) -> AdminModel | None:
        async with self.store.database.session_maker() as session:
            stm = select(AdminModel).where(AdminModel.email == email)
            return await session.scalar(stm)

    async def create_admin(self, email: str, password: str) -> AdminModel:
        async with self.store.database.session_maker() as session:
            admin = AdminModel(email=email, password=password)
            session.add(admin)
            try:
                await session.commit()
            except IntegrityError as e:
                logger.error(e)
                raise AdminCreateError(email) from e
            return admin

    async def delete_admin_by_email(self, email: str) -> None:
        async with self.store.database.session_maker() as session:
            stm = delete(AdminModel).where(AdminModel.email == email)
            await session.execute(stm)
            try:
                await session.commit()
            except SQLAlchemyError as e:
                logger.error(e)
                raise AdminDeleteError(email) from e
