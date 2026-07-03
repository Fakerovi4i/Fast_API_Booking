import pytest

from app.bookings.dao import BookingDAO
from datetime import datetime

from app.bookings.models import Bookings



@pytest.mark.parametrize("user_id, room_id", [
    (2,2),
    (2,3),
    (1,4),
    (1,4),
])
async def test_add_booking_dao(user_id, room_id):
    new_booking: Bookings = await BookingDAO.add(
        user_id=user_id,
        room_id=room_id,
        date_from=datetime.strptime("2023-07-10", "%Y-%m-%d"),
        date_to=datetime.strptime("2023-07-24", "%Y-%m-%d")
    )

    # CREATE
    assert new_booking.user_id == user_id
    assert new_booking.room_id == room_id

    # READ
    new_booking = await BookingDAO.find_by_id(new_booking.id)

    assert new_booking is not None

    # DELETE
    await BookingDAO.delete_booking(booking_id=new_booking.id, user_id=user_id)
    assert await BookingDAO.find_by_id(new_booking.id) is None



