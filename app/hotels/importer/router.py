from fastapi import UploadFile, APIRouter, HTTPException, status

from app.hotels.dao import HotelDAO

router = APIRouter(
    prefix="/import",
    tags=["Импорт SCV"]

)


@router.post("/hotels", status_code=status.HTTP_201_CREATED)
async def import_csv_hotels(file: UploadFile):
    # Проверяем, что файл CSV
    if not file.filename.endswith('.csv'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Файл должен быть в формате CSV"
        )

    content = await file.read()
    csv_data = content.decode('utf-8')

    await HotelDAO.import_from_csv(csv_data)









