from pydantic import BaseModel, ConfigDict
from datetime import date


class SBooking(BaseModel):
    id: int
    room_id: int
    user_id: int
    date_from: date
    date_to: date
    price: int
    total_cost: int
    total_days: int

    model_config = ConfigDict(from_attributes=True)
    # Это старый способ
    # class Config:
    #     orm_mode = True
    #     model_config = ConfigDict(from_attributes=True)

class SBookingReturn(BaseModel):

    model_config = ConfigDict(from_attributes=True)

    id: int
    room_id: int
    user_id: int
    date_from: date
    date_to: date
    price: int
    total_cost: int
    total_days: int
    image_id: int
    name: str
    description: str
    services: list[str]

    # class Config:
    #     orm_mode = True
