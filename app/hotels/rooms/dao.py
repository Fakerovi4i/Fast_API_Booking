from datetime import date

from sqlalchemy import select, func, and_, or_

from app.bookings.models import Bookings
from app.dao.base import BaseDAO
from app.database import async_session_maker
from app.hotels.rooms.models import Rooms
from app.hotels.rooms.schemas import SRoomWithBookingInfo


class RoomDAO(BaseDAO):
    model = Rooms

    @classmethod
    async def get_rooms_with_bookings_info(
            cls,
            hotel_id: int,
            date_from: date,
            date_to: date
    ) -> list[SRoomWithBookingInfo]:
        async with async_session_maker() as session:
            # Получаем все комнаты отеля
            rooms_query = select(Rooms).where(Rooms.hotel_id == hotel_id)
            rooms = await session.execute(rooms_query)
            rooms = rooms.scalars().all()

            result = []

            for room in rooms:
                booked_count_query = select(func.count(Bookings.id)).where(
                    and_(
                        Bookings.room_id == room.id,
                        or_(
                            # Бронирование начинается в период
                            and_(
                                Bookings.date_from >= date_from,
                                Bookings.date_from <= date_to
                            ),
                            # Бронирование заканчивается в период
                            and_(
                                Bookings.date_from <= date_from,
                                Bookings.date_to > date_from
                            )
                        )
                    )
                )

                booked_count = await session.execute(booked_count_query)
                booked_count = booked_count.scalar() or 0

                rooms_left = room.quantity - booked_count

                # Вычисляем стоимость бронирования за весь период
                days = (date_to - date_from).days
                total_cost = days * room.price if days > 0 else 0

                result.append(
                    SRoomWithBookingInfo(
                        id=room.id,
                        hotel_id=room.hotel_id,
                        name=room.name,
                        description=room.description,
                        services=room.services,
                        price=room.price,
                        quantity=room.quantity,
                        image_id=room.image_id,
                        total_cost=total_cost,
                        rooms_left=rooms_left if rooms_left > 0 else 0
                    )
                )

        return result

















