from fastapi.encoders import jsonable_encoder

from app.exceptions.users_exceptions import EmailAlreadyExists, IdAlreadyExists
from app.schemas.users.user import UserSchema

from ..commontest import create_headers


async def test_create_user(client):
    user_id = "aasjdfvhasdvnlaksdj123456789"
    create_user = UserSchema(name="Lio", lastname="Messi", email="email@email.com")
    response = await client.post("/users", json=jsonable_encoder(create_user), headers=create_headers(user_id))
    assert response.status_code == 201
    response_data = response.json()
    assert response_data == user_id

    response = await client.get(f"/users/{user_id}", headers=create_headers(user_id))
    assert response.status_code == 200
    assert response.json()["name"] == create_user.name
    assert response.json()["email"] == create_user.email
    assert response.json()["lastname"] == create_user.lastname


async def test_create_same_email_fails(client, create_user):
    new_user_same_email = create_user.copy()
    new_user_same_email.pop("id")
    caller_id = "otherid123456789909876543123"
    response = await client.post("/users", json=new_user_same_email, headers=create_headers(caller_id))

    expected_error = EmailAlreadyExists(create_user["email"])
    assert response.status_code == 409
    assert response.json()["detail"] == expected_error.detail


async def test_create_same_user_twice_fails(client, create_user):
    create_user["email"] = "other-email@email.com"
    caller_id = create_user.pop("id")
    response = await client.post("/users", json=create_user, headers=create_headers(caller_id))

    expected_error = IdAlreadyExists(caller_id)
    assert response.status_code == 409
    assert response.json()["detail"] == expected_error.detail


async def test_create_empty_user_fails(client):
    empty_user = {"name": "", "lastname": "", "email": ""}
    response = await client.post("/users", json=empty_user, headers=create_headers("avalidid12345678901234567890"))
    assert response.status_code == 422


async def test_create_invalid_email_fails(client):
    user_invalid_email = {
        "name": "Juan",
        "lastname": "Perez",
        "email": "invalid_email.com",
    }
    response = await client.post(
        "/users", json=user_invalid_email, headers=create_headers("avalidid12345678901234567890")
    )

    assert response.status_code == 422


async def test_create_user_no_id_in_headers_fails(client):
    create_user = UserSchema(name="Lio", lastname="Messi", email="email@email.com")
    response = await client.post(
        "/users",
        json=jsonable_encoder(create_user),
    )
    assert response.status_code == 422
