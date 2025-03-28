from fastapi.encoders import jsonable_encoder

from app.schemas.events.roles import EventRole
from app.schemas.members.member_schema import MemberRequestSchema

from ..commontest import create_headers


async def test_get_chairs_with_new_chair(client, create_user, create_event_creator, create_event_from_event_creator):
    create_member_request = MemberRequestSchema(email=create_user["email"], role=EventRole.CHAIR)
    response = await client.post(
        f"/events/{create_event_from_event_creator}/members",
        json=jsonable_encoder(create_member_request),
        headers=create_headers(create_event_creator["id"]),
    )

    assert response.status_code == 201
    response = await client.get(
        f"/events/{create_event_from_event_creator}/chairs", headers=create_headers(create_event_creator["id"])
    )

    assert response.status_code == 200
    chair_list = response.json()
    assert len(chair_list) == 1
    unique_chair = chair_list[0]
    assert unique_chair["user_id"] == create_user["id"]
    assert len(unique_chair["tracks"]) == 0


async def test_get_chairs_empty(client, create_event_creator, create_event_from_event_creator):
    response = await client.get(
        f"/events/{create_event_from_event_creator}/chairs", headers=create_headers(create_event_creator["id"])
    )

    assert response.status_code == 200
    chair_list = response.json()
    assert len(chair_list) == 0


async def test_get_chair_by_user_id_being_myself_the_chair_and_organizer(
    client, create_event_from_event_creator, create_event_creator
):
    request = MemberRequestSchema(email=create_event_creator["email"], role=EventRole.CHAIR)
    # Add myself as chair
    response = await client.post(
        f"/events/{create_event_from_event_creator}/members",
        json=jsonable_encoder(request),
        headers=create_headers(create_event_creator["id"]),
    )
    assert response.status_code == 201

    response = await client.get(
        f"/events/{create_event_from_event_creator}/chairs/{create_event_creator['id']}",
        headers=create_headers(create_event_creator["id"]),
    )
    assert response.status_code == 200


async def test_get_chair_by_user_id_being_an_organizer(
    client, create_event_creator, create_event_from_event_creator, create_event_chair
):
    response = await client.get(
        f"/events/{create_event_from_event_creator}/chairs/{create_event_chair}",
        headers=create_headers(create_event_creator["id"]),
    )
    assert response.status_code == 200


async def test_get_chair_by_user_id_called_by_not_organizer_fails(
    client, create_event_from_event_creator, create_event_chair
):
    response = await client.get(
        f"/events/{create_event_from_event_creator}/chairs/{create_event_chair}",
        headers=create_headers(create_event_chair),
    )
    assert response.status_code == 403


async def test_get_chair_by_user_id_fails_if_the_user_does_not_exist(
    client,
    create_event_creator,
    create_event_from_event_creator,
):
    invalid_user_id = "qwertyuiopasdfghjklzxcvbnmdfghj"
    response = await client.get(
        f"/events/{create_event_from_event_creator}/chairs/{invalid_user_id}",
        headers=create_headers(create_event_creator["id"]),
    )
    assert response.status_code == 404


async def test_get_chair_by_user_id_fails_if_the_user_does_not_exist_as_chair(
    client,
    create_event_creator,
    create_event_from_event_creator,
    create_user,
):
    response = await client.get(
        f"/events/{create_event_from_event_creator}/chairs/{create_user['id']}",
        headers=create_headers(create_event_creator["id"]),
    )
    assert response.status_code == 404


async def test_get_chair_me_i_am_event_chair(client, create_event_from_event_creator, create_event_chair):
    response = await client.get(
        f"/events/{create_event_from_event_creator}/chairs/me", headers=create_headers(create_event_chair)
    )
    assert response.status_code == 200
    assert len(response.json()["tracks"]) == 0


async def test_get_chair_me_i_am_not_event_chair_fails(client, create_event_from_event_creator, create_user):
    response = await client.get(
        f"/events/{create_event_from_event_creator}/chairs/me", headers=create_headers(create_user["id"])
    )
    assert response.status_code == 403
