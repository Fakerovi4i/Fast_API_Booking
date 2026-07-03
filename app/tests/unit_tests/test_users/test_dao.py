from app.users.dao import UserDAO
import pytest



@pytest.mark.parametrize("user_id, email, is_exist", [
    (1, "test@test.com", True),
    (2, "test1@test1.com", True),
    (3, "test2@test2.com", False)
])
async def test_find_by_id(user_id, email, is_exist):
    user = await UserDAO.find_by_id(user_id)

    if is_exist:
        assert user
        assert user.id == user_id
        assert user.email == email
    else:
        assert not user
