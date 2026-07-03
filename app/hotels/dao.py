import json
from datetime import date
import io
import csv

from fastapi import HTTPException, status
from sqlalchemy import update, delete, select, and_, func, or_

from app.bookings.models import Bookings
from app.dao.base import BaseDAO
from app.database import async_session_maker
from app.exceptions import HotelAlreadyExistsException, HotelNotFoundException
from app.hotels.models import Hotels
from app.hotels.rooms.models import Rooms
from app.hotels.schemas import SHotelArgs, SHotel, SHotelAdd, SHotelWithRoomsLeft


class HotelDAO(BaseDAO):
    model = Hotels

    @classmethod
    async def change_hotel(cls, hotel_id: int, data: SHotelArgs) -> SHotel:
        update_data = data.model_dump(exclude_unset=True)
        async with async_session_maker() as session:
            hotel = await session.get(Hotels, hotel_id)
            if not hotel:
                raise HotelNotFoundException()

            for key, value in update_data.items():
                setattr(hotel, key, value)

            await session.commit()
            await session.refresh(hotel)
            return hotel


    @classmethod
    async def delete_hotel(cls, hotel_id: int):
        async with async_session_maker() as session:
            deleting_hotel = delete(Hotels).where(Hotels.id == hotel_id)
            await session.execute(deleting_hotel)
            await session.commit()
            return True

    @classmethod
    async def add(cls, data: SHotelAdd):
        existing_hotel = await HotelDAO.find_one_or_none(name=data.name, location=data.location)
        if existing_hotel:
            raise HotelAlreadyExistsException()

        async with async_session_maker() as session:
            new_hotel = Hotels(**data.model_dump())
            print(new_hotel)
            session.add(new_hotel)
            await session.commit()
            return new_hotel

    @classmethod
    async def find_hotels_by_location_with_rooms_left(
            cls,
            location: str,
            date_from: date,
            date_to: date
    ) -> list[SHotelWithRoomsLeft]:
        async with async_session_maker() as session:
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

            return hotels_with_rooms_left

    @classmethod
    async def find_by_id(cls, model_id: int):
        async with async_session_maker() as session:
            query = select(Hotels).filter_by(id=model_id)
            result = await session.execute(query)

            return result.scalar_one_or_none()

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





