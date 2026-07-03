from datetime import date
from typing import Optional

from fastapi import HTTPException
from sqlalchemy import and_, func, insert, or_, select

from app.bookings.models import Bookings
from app.bookings.schemas import SBookingReturn
from app.dao.base import BaseDAO
from app.database import async_session_maker
from app.exceptions import (
    BookingNotBelongsToUserException,
    BookingNotFoundException,
)
from app.hotels.rooms.models import Rooms


class BookingDAO(BaseDAO):
    model = Bookings

    @classmethod
    async def delete_booking(cls, booking_id: int, user_id: int):
        async with async_session_maker() as session:
            booking = await session.get(Bookings, booking_id)
            if not booking:
                raise BookingNotFoundException

            if booking.user_id != user_id:
                raise BookingNotBelongsToUserException

            await session.delete(booking)
            await session.commit()

    @classmethod
    async def find_all_with_room_info(
        cls, user_id: int
    ) -> Optional[list[SBookingReturn]]:
        async with async_session_maker() as session:
            query = (
                select(Bookings, Rooms)
                .join(Rooms, Rooms.id == Bookings.room_id)
                .where(Bookings.user_id == user_id)
            )

            result = await session.execute(query)
            bookings_rooms = result.all()
            data = [
                SBookingReturn(
                    id=booking.id,
                    room_id=booking.room_id,
                    user_id=booking.user_id,
                    date_from=booking.date_from,
                    date_to=booking.date_to,
                    price=booking.price,
                    total_cost=booking.total_cost,
                    total_days=booking.total_days,
                    image_id=room.image_id,
                    name=room.name,
                    description=room.description,
                    services=room.services or [],
                )
                for booking, room in bookings_rooms
            ]
            if not data:
                raise HTTPException(
                    status_code=404, detail="Bookings not found"
                )

            return data

    @classmethod
    async def add(
        cls, user_id: int, room_id: int, date_from: date, date_to: date
    ):

        async with async_session_maker() as session:
            booked_rooms = (
                select(Bookings)
                .where(
                    and_(
                        Bookings.room_id == room_id,
                        or_(
                            and_(
                                Bookings.date_from >= date_from,
                                Bookings.date_from <= date_to,
                            ),
                            and_(
                                Bookings.date_from <= date_from,
                                Bookings.date_to > date_from,
                            ),
                        ),
                    )
                )
                .cte("booked_rooms")
            )

            get_rooms_left = (
                select(
                    (
                        Rooms.quantity - func.count(booked_rooms.c.room_id)
                    ).label("rooms_left")
                )
                .select_from(Rooms)
                .join(
                    booked_rooms,
                    booked_rooms.c.room_id == Rooms.id,
                    isouter=True,
                )
                .where(Rooms.id == room_id)
                .group_by(Rooms.quantity, booked_rooms.c.room_id)
            )

            # print(get_rooms_left.compile(engine, compile_kwargs={"literal_binds": True}))

            rooms_left = await session.execute(get_rooms_left)
            rooms_left: int = rooms_left.scalar()

            if rooms_left > 0:
                get_price = select(Rooms.price).filter_by(id=room_id)
                price = await session.execute(get_price)
                price: int = price.scalar()
                add_booking = (
                    insert(Bookings)
                    .values(
                        room_id=room_id,
                        user_id=user_id,
                        date_from=date_from,
                        date_to=date_to,
                        price=price,
                    )
                    .returning(Bookings)
                )

                new_booking = await session.execute(add_booking)
                await session.commit()
                return new_booking.scalar()
            else:
                return None

