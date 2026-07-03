from datetime import date

from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi import BackgroundTasks
from typing import Optional

from app.bookings.dao import BookingDAO
from app.bookings.schemas import SBookingReturn, SBooking
from app.exceptions import RoomCannotBeBookedException
from app.tasks.tasks import send_booking_confirmation_email
from app.users.dependences import get_current_user
from app.users.models import Users

router = APIRouter(
    prefix="/bookings",
    tags=["Бронирования"]
)


@router.get("")
async def get_bookings(user: Users = Depends(get_current_user)) -> Optional[list[SBookingReturn]]:
    return await BookingDAO.find_all_with_room_info(user_id=user.id)

@router.post("")
async def add_booking(
        background_tasks: BackgroundTasks,
        room_id: int = Query(examples=["1"]),
        date_from: date = Query(examples=["2023-05-20"]),
        date_to: date = Query(examples=["2023-06-20"]),
        user: Users = Depends(get_current_user)
    ):
    try:
        booking = await BookingDAO.add(user.id, room_id, date_from, date_to)
        if not booking:
            raise RoomCannotBeBookedException
        if date_from > date_to:
            raise HTTPException(status_code=400, detail="Date from must be less than date to")

        booking_dict = SBooking.model_validate(booking).model_dump()
        # Celery вариант
        # send_booking_confirmation_email.delay(booking_dict, user.email)
        # Вариант с BackgroundTasks
        background_tasks.add_task(send_booking_confirmation_email, booking_dict, user.email)
        return booking_dict
    except (RoomCannotBeBookedException, Exception) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{booking_id}", status_code=204)
async def delete_booking(
        booking_id: int,
        user: Users = Depends(get_current_user)
    ):

    await BookingDAO.delete_booking(booking_id, user.id)
    return True







