from httpx import AsyncClient
import pytest


@pytest.mark.parametrize(
    "email, password, status_code", [
        ("kot@pes.com", "kotopes", 200),
        ("kot@pes.com", "kotopes", 409),
        ("pes@pes.com", "pesokot", 200),
        ("abgd", "pesokot", 422),
    ])
async def test_register_user(email, password, status_code, ac: AsyncClient):
    response = await ac.post("/auth/register", json={
        "email": email,
        "password": password
    })
    print("\n\n====================")
    print(response)
    print("====================\n")
    assert response.status_code == status_code


@pytest.mark.parametrize(
    "email, password, status_code",
    [
    ("test@test.com", "test", 200),
    ("test1@test1.com", "test1234", 401),
    ("test1@test1.com", "test1", 200)
    ])
async def test_login_user(email, password, status_code, ac: AsyncClient):
    response = await ac.post("/auth/login", json={
        "email": email,
        "password": password
    })

    print("\n\n====================")
    print(response)
    print("====================\n\n")
    assert response.status_code == status_code

