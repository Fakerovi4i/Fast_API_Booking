import csv
import io
from typing import Literal

from fastapi import UploadFile, APIRouter, HTTPException, status, Depends

from app.dao.base import BaseDAO
from app.users.dependences import get_current_user
from app.importer.utils import TABLE_MODEL_MAP, convert_csv_to_postgres_format

router = APIRouter(
    prefix="/import",
    tags=["Импорт данных из CSV базу"]

)


@router.post(
    "/{table_name}",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(get_current_user)]
)
async def import_csv_table(
        file: UploadFile,
        table_name: Literal["hotels", "rooms", "bookings"]
):
    if not file.filename.endswith('.csv'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Файл должен быть в формате CSV"
        )
    ModelDAO: type[BaseDAO] = TABLE_MODEL_MAP[table_name]
    content = (await file.read()).decode('utf-8')
    csvReader = csv.DictReader(io.StringIO(content), delimiter=';')
    data = convert_csv_to_postgres_format(csvReader)

    if not data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Файл не содержит данных"
        )

    if table_name == "bookings":
        for row in data:
            row.pop("total_cost", None)
            row.pop("total_days", None)

    inserted = await ModelDAO.add_many_from_csv(data)
    return {"message": f"Добавлено {inserted} записей"}


