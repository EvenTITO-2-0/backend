from uuid import uuid4

from fastapi.encoders import jsonable_encoder

from app.schemas.users.user import UserSchema

from ..commontest import create_headers

USERS = [
    UserSchema(
        name="Lucia",
        lastname="Benitez",
        email="lbenitez@email.com",
    ),
    UserSchema(
        name="Marta",
        lastname="Benitez",
        email="mbenitez@email.com",
    ),
    UserSchema(
        name="Pedro",
        lastname="Benitez",
        email="pbenitez@email.com",
    ),
]


async def create_all_users(client):
    ids = []
    for user in USERS:
        uid = str(uuid4())
        id = 3 * uid[0:8] + "asdf"  # just a random UID, not UUID because it fails validation.
        await client.post("/users", json=jsonable_encoder(user), headers=create_headers(id))
        ids.append(id)
    return ids


async def test_get_all_users(client, admin_data):
    ids = await create_all_users(client)
    response = await client.get("/users", headers=create_headers(admin_data.id))
    assert response.status_code == 200
    all_users = response.json()

    ids.append(admin_data.id)
    assert len(all_users) == len(ids)
    for user in all_users:
        assert user["id"] in ids


async def test_get_all_users_non_admin_fails(client, create_user):
    await create_all_users(client)
    response = await client.get("/users", headers=create_headers(create_user["id"]))
    assert response.status_code == 403
