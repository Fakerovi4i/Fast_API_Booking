from datetime import date

from sqlalchemy import delete, select, and_, func, or_
from sqlalchemy.exc import SQLAlchemyError

from app.bookings.models import Bookings
from app.dao.base import BaseDAO
from app.database import async_session_maker
from app.exceptions import HotelAlreadyExistsException, HotelNotFoundException, DatabaseErrorException
from app.hotels.models import Hotels
from app.hotels.rooms.models import Rooms
from app.hotels.schemas import SHotelArgs, SHotel, SHotelAdd, SHotelWithRoomsLeft
from app.logger import logger


class HotelDAO(BaseDAO):
    """
    Вместо общего метода для всех таблиц, можно сделать более просто для каждой таблицы
    @classmethod
    async def import_from_csv(cls, csv_data: str):
        csv_reader = csv.DictReader(io.StringIO(csv_data))

        hotels_to_add = []
        for row in csv_reader:
            name = row.get('name')
            location = row.get('location')
            existing_hotel = await cls.find_one_or_none(name=name, location=location)
            if existing_hotel:
                continue

            services_str = row.get('services', '[]')
            try:
                services = json.loads(services_str)
            except json.JSONDecodeError:
                services = []


            hotel = {
                "name": name,
                "location": location,
                "services": services,
                "rooms_quantity": int(row.get("rooms_quantity", 0)),
                "image_id": int(row.get("image_id", 0))
            }
            hotels_to_add.append(hotel)

        if not hotels_to_add:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="CSV файл не содержит новых данных"
            )

        async with async_session_maker() as session:
            for hotel_data in hotels_to_add:
                hotel = Hotels(**hotel_data)
                session.add(hotel)
            await session.commit()
    """

    model = Hotels

    @classmethod
    async def change_hotel(cls, hotel_id: int, data: SHotelArgs) -> SHotel:
        # exclude_unset=True - этот флаг позволяет не передавать в update
        # значения, которые не изменились
        update_data = data.model_dump(exclude_unset=True)
        async with async_session_maker() as session:
            try:
                hotel = await session.get(Hotels, hotel_id)
                if not hotel:
                    raise HotelNotFoundException()

                for key, value in update_data.items():
                    setattr(hotel, key, value)

                await session.commit()
                await session.refresh(hotel)
                logger.info(f"HOTEL UPDATED: id={hotel_id}, user={hotel.name}")
                return hotel
            except SQLAlchemyError as e:
                logger.error(f"CHANGE HOTEL ERROR: {e}", exc_info=True)
                await session.rollback()
                raise DatabaseErrorException from e



    @classmethod
    async def delete_hotel(cls, hotel_id: int):
        async with async_session_maker() as session:
            try:
                deleting_hotel = delete(Hotels).where(Hotels.id == hotel_id)
                await session.execute(deleting_hotel)
                await session.commit()
                logger.info(f"HOTEL DELETED: id={hotel_id}")
                return True
            except SQLAlchemyError as e:
                logger.error(f"DELETE HOTEL ERROR: {e}", exc_info=True)
                await session.rollback()
                raise DatabaseErrorException from e

    @classmethod
    async def add(cls, data: SHotelAdd):
        async with async_session_maker() as session:
            try:
                existing_hotel = await session.execute(
                    select(Hotels).filter_by(name=data.name, location=data.location)
                )
                if existing_hotel.scalar_one_or_none():
                    raise HotelAlreadyExistsException()

                new_hotel = Hotels(**data.model_dump())
                session.add(new_hotel)
                await session.commit()
                logger.info(f"HOTEL ADDED: id={new_hotel.id}, name={new_hotel.name}")
                return new_hotel
            except SQLAlchemyError as e:
                logger.error(f"ADD HOTEL ERROR: {e}", exc_info=True)
                await session.rollback()
                raise DatabaseErrorException from e

    @classmethod
    async def find_hotels_by_location_with_rooms_left(
            cls,
            location: str,
            date_from: date,
            date_to: date
    ) -> list[SHotelWithRoomsLeft]:
        async with async_session_maker() as session:
            try:
                hotels_query = select(Hotels).where(
                    and_(
                        Hotels.rooms_quantity > 0,
                        Hotels.location.ilike(f"%{location}%")
                    )
                )
                hotels = await session.execute(hotels_query)
                hotels = hotels.scalars().all()

                hotels_with_rooms_left = []

                for hotel in hotels:
                    # Получаем все комнаты отеля
                    rooms_query = select(Rooms.id).where(Rooms.hotel_id == hotel.id)
                    rooms = await session.execute(rooms_query)
                    room_ids = [room[0] for room in rooms.all()]

                    if not room_ids:
                        # Если нет комнат, то свободных номеров 0
                        continue

                    booked_rooms_query = select(func.count(Bookings.id)).where(
                        and_(
                            Bookings.room_id.in_(room_ids),
                            or_(
                                and_(
                                    Bookings.date_from >= date_from,
                                    Bookings.date_from <= date_to
                                ),
                                and_(
                                    Bookings.date_from <= date_from,
                                    Bookings.date_to > date_from
                                )
                            )
                        )
                    )

                    booked_count = await session.execute(booked_rooms_query)
                    booked_count = booked_count.scalar() or 0

                    # Вычисляем свободные номера
                    rooms_left = hotel.rooms_quantity - booked_count

                    if rooms_left > 0:
                        hotels_with_rooms_left.append(
                            SHotelWithRoomsLeft(
                                id=hotel.id,
                                name=hotel.name,
                                location=hotel.location,
                                services=hotel.services,
                                rooms_quantity=hotel.rooms_quantity,
                                image_id=hotel.image_id,
                                rooms_left=rooms_left
                            )
                        )
                logger.info(f"FIND HOTELS WITH ROOMS LEFT SUCCESS: {len(hotels_with_rooms_left)} hotels found")
                return hotels_with_rooms_left
            except SQLAlchemyError as e:
                logger.error(f"FIND HOTELS WITH ROOMS LEFT ERROR: params {location}, {date_from}, {date_to}, {e}", exc_info=True)
                raise DatabaseErrorException from e


    @classmethod
    async def find_all(cls) -> list[SHotel]:
        async with async_session_maker() as session:
            try:
                query = select(Hotels)
                result = await session.execute(query)
                logger.info("FIND ALL SUCCESS")
                return result.scalars().all()
            except SQLAlchemyError as e:
                logger.error(f"FIND ALL ERROR: {e}", exc_info=True)
                raise DatabaseErrorException from e





