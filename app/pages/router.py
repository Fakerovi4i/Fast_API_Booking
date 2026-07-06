from fastapi import APIRouter, status, Request, Depends
from fastapi.templating import Jinja2Templates

from app.hotels.router import get_hotels_by_location_and_time
from app.hotels.dao import HotelDAO

router = APIRouter(prefix="/pages", tags=["Фронтенд"])


templates = Jinja2Templates(directory="app/templates")

@router.get("/hotels", status_code=status.HTTP_200_OK)
async def get_hotels_page_with_filter(
        request: Request,
        hotels=Depends(get_hotels_by_location_and_time)
):
    return templates.TemplateResponse(
        name="hotels.html",
        context={"request": request, "hotels": hotels}
    )

@router.get("/hotels/all", status_code=status.HTTP_200_OK)
async def get_all_hotels(
        request: Request,
        hotels=Depends(HotelDAO.find_all)
):
    return templates.TemplateResponse(
        name="hotels.html",
        context={"request": request, "hotels": hotels}
    )
