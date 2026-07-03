from httpx import AsyncClient
import json

async def test_get_bookings_api(authenticated_ac: AsyncClient
):
    response = await authenticated_ac.get("/bookings")

    assert response.status_code == 200

    for booking in response.json():
        response = await authenticated_ac.delete(f"/bookings/{int(booking['id'])}")

        assert response.status_code == 204

    response = await authenticated_ac.get("/bookings")

    assert response.status_code == 404

    # print(json.dumps(response.json(), indent=2, ensure_ascii=False))

