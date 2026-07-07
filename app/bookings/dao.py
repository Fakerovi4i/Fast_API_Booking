from datetime import date
from typing import Optional

from sqlalchemy import and_, func, insert, or_, select
from sqlalchemy.exc import SQLAlchemyError

from app.logger import logger
from app.bookings.models import Bookings
from app.bookings.schemas import SBookingReturn
from app.dao.base import BaseDAO
from app.database import async_session_maker
from app.exceptions import (
    BookingNotBelongsToUserException,
    BookingNotFoundException,
    DatabaseErrorException, RoomCannotBeBookedException
)
from app.hotels.rooms.models import Rooms


class BookingDAO(BaseDAO):
    model = Bookings

    @classmethod
    async def delete_booking(cls, booking_id: int, user_id: int):
        async with async_session_maker() as session:
            try:
                logger.info(f"TRYING TO DELETE BOOKING: {booking_id}")
                booking = await session.get(Bookings, booking_id)
                if not booking:
                    raise BookingNotFoundException()
                if booking.user_id != user_id:
                    raise BookingNotBelongsToUserException()
                await session.delete(booking)
                await session.commit()
                logger.info(f"Booking deleted: id={booking_id}")
            except SQLAlchemyError as e:
                logger.error(f"Database error in delete_booking: {e}")
                await session.rollback()
                raise DatabaseErrorException() from e

    @classmethod
    async def find_all_with_room_info(
        cls, user_id: int
    ) -> Optional[list[SBookingReturn]]:
        async with async_session_maker() as session:
            try:
                logger.info(f"TRYING TO FIND ALL BOOKINGS WITH ROOM INFO: {user_id}")
                query = (
                    select(Bookings, Rooms)
                    .join(Rooms, Rooms.id == Bookings.room_id)
                    .where(Bookings.user_id == user_id)
                )

                result = await session.execute(query)
                bookings_rooms = result.all()

                if not bookings_rooms:
                    raise BookingNotFoundException()

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
                logger.info(f"Found {len(data)} bookings for user {user_id}")
                return data
            except SQLAlchemyError as e:
                logger.error(f"Database error in find_all_with_room_info: {e}")
                raise DatabaseErrorException() from e

    @classmethod
    async def add(
            cls, user_id: int, room_id: int, date_from: date, date_to: date
        ):
            async with async_session_maker() as session:
                logger.info(f"TRYING TO ADD BOOKING: {user_id}, {room_id}, {date_from}, {date_to}")
                try:
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

                    rooms_left = await session.execute(get_rooms_left)
                    rooms_left: int = rooms_left.scalar()

                    if rooms_left is None or rooms_left <= 0:
                        raise RoomCannotBeBookedException()

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
                    booking = new_booking.scalar()
                    logger.info(f"Booking created: id={booking.id}, user={user_id}, room={room_id}")
                    return booking
                except SQLAlchemyError as e:
                    logger.error(f"Database error in add: {e}")
                    await session.rollback()
                    raise DatabaseErrorException() from e


