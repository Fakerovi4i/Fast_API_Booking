from typing import Optional

from pydantic import BaseModel

class SHotel(BaseModel):
    id: int
    name: str
    location: str
    services: Optional[list[str]]
    rooms_quantity: int
    image_id: int

class SHotelArgs(BaseModel):
    name: Optional[str] = None
    location: Optional[str] = None
    services: Optional[list[str]] = None
    rooms_quantity: Optional[int] = None
    image_id: Optional[int] = None

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "Гостиница Алтай",
                    "location": "Республика Алтай",
                    "services": ["Wi-Fi", "Бассейн", "Парковка"],
                    "rooms_quantity": 25,
                    "image_id": 1
                }
            ]
        }
    }

class SHotelAdd(BaseModel):
    name: str
    location: str
    services: Optional[list[str]] = None
    rooms_quantity: int
    image_id: int

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "Гостиница Алтай",
                    "location": "Республика Алтай",
                    "services": ["Wi-Fi", "Бассейн", "Парковка"],
                    "rooms_quantity": 25,
                    "image_id": 1
                }
            ]
        }
    }


class SHotelWithRoomsLeft(SHotel):
    rooms_left: int


