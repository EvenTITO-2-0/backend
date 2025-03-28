from fastapi.encoders import jsonable_encoder

from app.schemas.users.user import UserSchema

from ..commontest import create_headers


async def test_put_user(client, create_user):
    update_create_user = create_user.copy()
    update_create_user["name"] = "new name"
    update_create_user["lastname"] = "new lastname"
    update_create_user["identification_number"] = "1234"
    update_create_user["phone"] = "5491165501111"
    update_create_user["address"] = "Paseo Colon 850"
    update_create_user["city"] = "Ciudad de Buenos Aires"
    update_create_user["country"] = "Argentina"
    caller_id = update_create_user.pop("id")
    response = await client.put(f"/users/{caller_id}", json=update_create_user, headers=create_headers(caller_id))

    assert response.status_code == 204
    response = await client.get(f"/users/{caller_id}", headers=create_headers(caller_id))
    assert response.status_code == 200
    assert response.json()["name"] == update_create_user["name"]
    assert response.json()["email"] == update_create_user["email"]
    assert response.json()["lastname"] == update_create_user["lastname"]
    assert response.json()["identification_number"] == update_create_user["identification_number"]
    assert response.json()["address"] == update_create_user["address"]
    assert response.json()["city"] == update_create_user["city"]
    assert response.json()["country"] == update_create_user["country"]


async def test_put_user_not_exists(client, create_user):
    user_changes = create_user.copy()
    different_id = "thisiddoesnotexist1234567890"
    new_lastname = "Rocuzzo"
    user_changes.pop("id")
    user_changes["lastname"] = new_lastname
    response = await client.put("/users/other-user-id", json=user_changes, headers=create_headers(different_id))
    assert response.status_code == 404


async def test_email_cant_change(client, create_user):
    update_create_user = create_user.copy()
    update_create_user["email"] = "nuevo_email@gmail.com"
    caller_id = update_create_user.pop("id")
    response = await client.put(f"/users/{caller_id}", json=update_create_user, headers=create_headers(caller_id))

    response = await client.get(f"/users/{caller_id}", headers=create_headers(caller_id))

    assert response.json()["email"] == create_user["email"]


async def test_user_cant_change_other_user(client, create_user):
    other = UserSchema(
        name="Lio",
        lastname="Messi",
        email="other_user@email.com",
    )
    other_user_id = "iasdiohvklaspiolsds123456789"
    response = await client.post("/users", json=jsonable_encoder(other), headers=create_headers(other_user_id))
    assert response.status_code == 201

    update_create_user = create_user.copy()
    update_create_user["email"] = "nuevo_email@gmail.com"
    caller_id = update_create_user.pop("id")
    response = await client.put(f"/users/{other_user_id}", json=update_create_user, headers=create_headers(caller_id))

    assert response.status_code == 403


async def test_admin_user_can_change_other_user(client, create_user, admin_data):
    update_create_user = create_user.copy()
    update_create_user["name"] = "Martina"
    caller_id = update_create_user.pop("id")
    response = await client.put(f"/users/{caller_id}", json=update_create_user, headers=create_headers(admin_data.id))

    assert response.status_code == 204
