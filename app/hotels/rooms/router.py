from datetime import date

from fastapi import APIRouter, Path, Query

from app.exceptions import WrongDateException, HotelNotFoundException
from app.hotels.dao import HotelDAO
from app.hotels.rooms.dao import RoomDAO
from app.hotels.rooms.schemas import SRoomWithBookingInfo

router = APIRouter(prefix="", tags=["Отели"])

@router.get("/{hotel_id}/rooms")
async def get_hotel_rooms(
        hotel_id: int = Path(examples=["1"]),
        date_from: date = Query(examples=["2023-05-20"]),
        date_to: date = Query(examples=["2023-06-20"])
) -> list[SRoomWithBookingInfo]:
    if date_from >= date_to:
        raise WrongDateException

    hotel = await HotelDAO.find_by_id(hotel_id)
    if not hotel:
        raise HotelNotFoundException

    return await RoomDAO.get_rooms_with_bookings_info(hotel_id, date_from, date_to)