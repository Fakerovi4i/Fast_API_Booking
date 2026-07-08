from datetime import date, timedelta

from fastapi import APIRouter, Path, Query, status
from app.exceptions import HotelNotFoundException, WrongDateException
from app.hotels.dao import HotelDAO
from app.hotels.schemas import SHotel, SHotelAdd, SHotelArgs, SHotelWithRoomsLeft
from app.hotels.rooms.router import router as router_hotels_rooms


router_hotels = APIRouter(prefix="/hotels", tags=["Отели"])
router_hotels.include_router(router_hotels_rooms)

router_admin_hotels = APIRouter(prefix="/hotels", tags=["Управление Отелями"])

@router_hotels.get("/{hotel_id}")
async def get_hotel_by_id(hotel_id: int) -> SHotel:
    hotel = await HotelDAO.find_by_id(hotel_id)
    if not hotel:
        raise HotelNotFoundException()
    return hotel


@router_hotels.get("")
async def get_hotels_by_location_and_time(
    location: str = Query(
        example="Алтай"
    ),
    date_from: date = Query(example="2023-05-20"),
    date_to: date = Query(example="2023-06-20")
) -> list[SHotelWithRoomsLeft]:
    if (date_from >= date_to) or (date_to - date_from > timedelta(days=60)):
        raise WrongDateException()
    hotels = await HotelDAO.find_hotels_by_location_with_rooms_left(location, date_from, date_to)
    return hotels



@router_admin_hotels.post("", status_code=status.HTTP_201_CREATED)
async def add_hotel(data: SHotelAdd) -> SHotel:
    return await HotelDAO.add(data)

@router_admin_hotels.delete("")
async def delete_hotel(hotel_id: int) -> None:
    return await HotelDAO.delete_hotel(hotel_id)


@router_admin_hotels.patch("/id/{hotel_id}", status_code=status.HTTP_201_CREATED)
async def update_hotel(
        hotel_id: int,
        data: SHotelArgs
) -> SHotel:
    return await HotelDAO.change_hotel(hotel_id, data)



