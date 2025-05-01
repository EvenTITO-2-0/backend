from fastapi.encoders import jsonable_encoder

from app.database.models.user import UserRole
from app.schemas.users.user import UserSchema
from app.schemas.users.user_role import UserRoleSchema

from ..commontest import create_headers, get_user_method


async def test_basic_user_has_DEFAULT(client, create_user):
    response = await client.get(f"/users/{create_user['id']}", headers=create_headers(create_user["id"]))
    assert response.status_code == 200
    assert response.json()["role"] == UserRole.DEFAULT.value


async def test_admin_can_change_default_role_to_admin(client, create_user, admin_data):
    new_role = UserRoleSchema(role=UserRole.ADMIN.value)
    response = await client.patch(
        f"/users/{create_user['id']}/roles", json=jsonable_encoder(new_role), headers=create_headers(admin_data.id)
    )

    assert response.status_code == 204
    user = await get_user_method(client, create_user["id"])

    assert user["id"] == create_user["id"]
    assert user["role"] == UserRole.ADMIN.value


async def test_change_role_to_event_creator(client, create_user, admin_data):
    new_role = UserRoleSchema(role=UserRole.EVENT_CREATOR.value)
    response = await client.patch(
        f"/users/{create_user['id']}/roles", json=jsonable_encoder(new_role), headers=create_headers(admin_data.id)
    )
    assert response.status_code == 204
    user = await get_user_method(client, create_user["id"])
    assert user["id"] == create_user["id"]
    assert user["role"] == UserRole.EVENT_CREATOR.value


async def test_admin_deletes_other_admin_role(client, create_user, admin_data):
    # changes create_user to ADMIN
    new_role = UserRoleSchema(role=UserRole.ADMIN.value)
    _ = await client.patch(
        f"/users/{create_user['id']}/roles", json=jsonable_encoder(new_role), headers=create_headers(admin_data.id)
    )

    # changes create_user to DEFAULT
    new_role = UserRoleSchema(role=UserRole.DEFAULT.value)
    response = await client.patch(
        f"/users/{create_user['id']}/roles", json=jsonable_encoder(new_role), headers=create_headers(admin_data.id)
    )

    assert response.status_code == 204

    user = await get_user_method(client, create_user["id"])
    assert user["role"] == UserRole.DEFAULT.value


async def test_admin_deletes_other_event_creator_role(client, create_user, admin_data):
    # changes create_user to EVENT_CREATOR
    new_role = UserRoleSchema(role=UserRole.EVENT_CREATOR.value)
    _ = await client.patch(
        f"/users/{create_user['id']}/roles", json=jsonable_encoder(new_role), headers=create_headers(admin_data.id)
    )

    # changes create_user to DEFAULT
    new_role = UserRoleSchema(role=UserRole.DEFAULT.value)
    response = await client.patch(
        f"/users/{create_user['id']}/roles", json=jsonable_encoder(new_role), headers=create_headers(admin_data.id)
    )

    assert response.status_code == 204
    user = await get_user_method(client, create_user["id"])
    assert user["role"] == UserRole.DEFAULT.value


async def test_not_admin_user_cant_add_admin(client, create_user):
    non_admin_user = UserSchema(name="Lio", lastname="Messi", email="email@email.com")
    non_admin_id = "idnonadmin123456789012345678"
    response = await client.post("/users", json=jsonable_encoder(non_admin_user), headers=create_headers(non_admin_id))
    new_role = UserRoleSchema(role=UserRole.ADMIN.value)
    response = await client.patch(
        f"/users/{create_user['id']}/roles", json=jsonable_encoder(new_role), headers=create_headers(non_admin_id)
    )
    assert response.status_code == 403


async def test_not_admin_user_cant_add_creator(client, create_user):
    non_admin_user = UserSchema(name="Lio", lastname="Messi", email="email@email.com")
    non_admin_id = "idnonadmin123456789012345678"
    response = await client.post("/users", json=jsonable_encoder(non_admin_user), headers=create_headers(non_admin_id))
    new_role = UserRoleSchema(role=UserRole.EVENT_CREATOR.value)
    response = await client.patch(
        f"/users/{create_user['id']}/roles", json=jsonable_encoder(new_role), headers=create_headers(non_admin_id)
    )
    assert response.status_code == 403


async def test_creator_user_cant_add_other_creator(client, create_user, admin_data):
    creator_role = UserRoleSchema(role=UserRole.EVENT_CREATOR.value)
    await client.patch(
        f"/users/{create_user['id']}/roles", json=jsonable_encoder(creator_role), headers=create_headers(admin_data.id)
    )

    default_role_user = UserSchema(name="Lio", lastname="Messi", email="email@email.com")
    default_user_id = "id-default-user"
    await client.post("/users", json=jsonable_encoder(default_role_user), headers=create_headers(default_user_id))

    response = await client.patch(
        f"/users/{default_user_id}/roles",
        json=jsonable_encoder(creator_role),
        headers=create_headers(create_user["id"]),
    )
    assert response.status_code == 403


async def test_user_without_roles_cant_delete_other_admin(client, create_user, admin_data):
    # user is trying to change admin_data to DEFAULT
    new_role = UserRoleSchema(role=UserRole.DEFAULT.value)
    response = await client.patch(
        f"/users/{admin_data.id}/roles", json=jsonable_encoder(new_role), headers=create_headers(create_user["id"])
    )

    assert response.status_code == 403


async def test_event_creator_cant_delete_other_admin(client, create_user, admin_data):
    # changes create_user to EVENT_CREATOR
    new_role = UserRoleSchema(role=UserRole.EVENT_CREATOR.value)
    _ = await client.patch(
        f"/users/{create_user['id']}/roles", json=jsonable_encoder(new_role), headers=create_headers(admin_data.id)
    )

    # user is trying to change admin_data to DEFAULT
    new_role = UserRoleSchema(role=UserRole.DEFAULT.value)
    response = await client.patch(
        f"/users/{admin_data.id}/roles", json=jsonable_encoder(new_role), headers=create_headers(create_user["id"])
    )

    assert response.status_code == 403


async def test_admin_can_change_self(client, create_user, admin_data):
    # add another admin
    new_role = UserRoleSchema(role=UserRole.ADMIN.value)
    _ = await client.patch(
        f"/users/{create_user['id']}/roles", json=jsonable_encoder(new_role), headers=create_headers(admin_data.id)
    )

    new_role = UserRoleSchema(role=UserRole.DEFAULT.value)
    response = await client.patch(
        f"/users/{admin_data.id}/roles", json=jsonable_encoder(new_role), headers=create_headers(admin_data.id)
    )

    assert response.status_code == 204

    user = await get_user_method(client, admin_data.id)
    assert user["role"] == UserRole.DEFAULT.value
