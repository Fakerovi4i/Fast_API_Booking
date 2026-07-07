from sqlalchemy import select, insert
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.exc import SQLAlchemyError

from app.database import async_session_maker
from app.exceptions import DatabaseErrorException
from app.logger import logger


class BaseDAO:
    model = None

    @classmethod
    async def find_by_id(cls, model_id: int):
        async with async_session_maker() as session:
            try:
                query = select(cls.model).filter_by(id=model_id)
                result = await session.execute(query)
                logger.info("FIND BY ID SUCCESS")
                return result.scalar_one_or_none()
            except SQLAlchemyError as e:
                logger.error(f"FIND BY ID ERROR: {e}", exc_info=True)
                raise DatabaseErrorException from e


    @classmethod
    async def find_one_or_none(cls, **filter_by):
        async with async_session_maker() as session:
            try:
                query = select(cls.model).filter_by(**filter_by)
                result = await session.execute(query)
                logger.info("FIND ONE OR NONE SUCCESS")
                return result.scalar_one_or_none()
            except SQLAlchemyError as e:
                logger.error(f"FIND ONE OR NONE ERROR: {e}", exc_info=True)
                raise DatabaseErrorException from e


    @classmethod
    async def find_all(cls, **filter_by):
        async with async_session_maker() as session:
            try:
                query = select(cls.model).filter_by(**filter_by)
                result = await session.execute(query)
                logger.info("FIND ALL SUCCESS")
                return result.scalars().all()
            except SQLAlchemyError as e:
                logger.error(f"FIND ALL ERROR: {e}", exc_info=True)
                raise DatabaseErrorException from e


    @classmethod
    async def add(cls, **data):
        async with async_session_maker() as session:
            try:
                query = insert(cls.model).values(**data)
                await session.execute(query)
                await session.commit()
                logger.info("ADD SUCCESS")
            except SQLAlchemyError as e:
                logger.error(f"ADD ERROR: {e}", exc_info=True)
                await session.rollback()
                raise DatabaseErrorException from e


    @classmethod
    async def add_many_from_csv(cls, data: list[dict]):
        async with async_session_maker() as session:
            try:
                query = pg_insert(cls.model).values(data).on_conflict_do_nothing()
                result = await session.execute(query)
                await session.commit()
                logger.info("ADD_MANY_FROM_CSV SUCCESS")
                return result.rowcount
            except SQLAlchemyError as e:
                logger.error(f"ADD_MANY_FROM_CSV ERROR: {e}", exc_info=True)
                await session.rollback()
                raise DatabaseErrorException from e





















