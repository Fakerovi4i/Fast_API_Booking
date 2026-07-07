from datetime import date

from fastapi import APIRouter, Depends, Query
from fastapi import BackgroundTasks

from app.bookings.dao import BookingDAO
from app.bookings.schemas import SBookingReturn, SBooking
from app.exceptions import WrongDateException
from app.logger import logger
from app.tasks.tasks import send_booking_confirmation_email
from app.users.dependences import get_current_user
from app.users.models import Users

router = APIRouter(
    prefix="/bookings",
    tags=["Бронирования"]
)


@router.get("")
async def get_bookings(user: Users = Depends(get_current_user)) -> list[SBookingReturn]:
    bookings = await BookingDAO.find_all_with_room_info(user_id=user.id)
    logger.info(f"User {user.email} retrieved {len(bookings)} bookings")
    return bookings

@router.post("")
async def add_booking(
        background_tasks: BackgroundTasks,
        room_id: int = Query(examples=["1"]),
        date_from: date = Query(examples=["2023-05-20"]),
        date_to: date = Query(examples=["2023-06-20"]),
        user: Users = Depends(get_current_user)
    ):
    if date_from > date_to:
        raise WrongDateException()

    booking = await BookingDAO.add(user.id, room_id, date_from, date_to)
    booking_dict = SBooking.model_validate(booking).model_dump()

    # Celery вариант
    # send_booking_confirmation_email.delay(booking_dict, user.email)

    # Вариант с BackgroundTasks
    background_tasks.add_task(send_booking_confirmation_email, booking_dict, user.email)
    return booking_dict


@router.delete("/{booking_id}", status_code=204)
async def delete_booking(
        booking_id: int,
        user: Users = Depends(get_current_user)
    ):
    await BookingDAO.delete_booking(booking_id, user.id)
    logger.info(f"Booking deleted: id={booking_id}, user={user.email}")
    return True







