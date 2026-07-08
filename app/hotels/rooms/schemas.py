from pydantic import BaseModel, ConfigDict
from typing import Optional

class SRoomWithBookingInfo(BaseModel):
    id: int
    hotel_id: int
    name: str
    description: Optional[str] = None
    price: int
    services: Optional[list[str]] = None
    quantity: int
    image_id: int
    rooms_left: int
    total_cost: int

    model_config = ConfigDict(from_attributes=True)