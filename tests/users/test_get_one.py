from fastapi.encoders import jsonable_encoder

from app.exceptions.users_exceptions import UserNotFound
from app.schemas.users.user import UserSchema

from ..commontest import create_headers


async def test_get_user(client, create_user):
    response = await client.get(f"/users/{create_user['id']}", headers=create_headers(create_user["id"]))
    assert response.status_code == 200
    assert response.json()["name"] == create_user["name"]


async def test_get_no_user_cant_get_other(client, create_user):
    new_user_id = "usernotexists123456789012345"

    response = await client.get(f"/users/{create_user['id']}", headers=create_headers(new_user_id))
    expected_error = UserNotFound(new_user_id)
    assert response.status_code == 404
    assert response.json()["detail"] == expected_error.detail


async def test_get_user_from_other_user_forbidden(client, create_user):
    other_user_id = "paoksncaokasdasdl12345678901"
    other_create_user = UserSchema(name="Lio", lastname="Messi", email="email@email.com")
    await client.post("/users", json=jsonable_encoder(other_create_user), headers=create_headers(other_user_id))

    response = await client.get(f"/users/{other_user_id}", headers=create_headers(create_user["id"]))
    assert response.status_code == 403


async def test_get_user_from_admin_user_success(client, create_user, admin_data):
    response = await client.get(f"/users/{create_user['id']}", headers=create_headers(admin_data.id))
    assert response.status_code == 200
