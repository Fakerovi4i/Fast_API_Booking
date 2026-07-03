import pytest
from httpx import AsyncClient
import json




@pytest.mark.parametrize("location, date_from, date_to, status_code", [
    ('Алтай', '2030-05-01', '2030-04-15', 400),
    ('Алтай', '2030-05-01', '2030-08-30', 400),
    ('Алтай', '2030-05-01', '2030-06-15', 200),

])
async def test_get_hotels_by_location_and_time_api(
        location,
        date_from,
        date_to,
        status_code,
        authenticated_ac: AsyncClient
):
    response = await authenticated_ac.get("/hotels", params={
        "location": location,
        "date_from": date_from,
        "date_to": date_to
    })

    assert response.status_code == status_code

    # data = response.json()
    # data = json.dumps(data, indent=2, ensure_ascii=False)
    # print("\n\n========================\n", data, "\n========================")

