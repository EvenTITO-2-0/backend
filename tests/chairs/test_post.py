from fastapi.encoders import jsonable_encoder

from app.exceptions.members.chair.chair_exceptions import UserNotIsChair
from app.schemas.events.roles import EventRole
from app.schemas.events.schemas import DynamicTracksEventSchema
from app.schemas.members.member_schema import MemberRequestSchema

from ..commontest import create_headers


async def test_creator_can_add_user_as_chair(
    client, create_event_creator, create_event_from_event_creator, create_user
):
    request = MemberRequestSchema(email=create_user["email"], role=EventRole.CHAIR)
    response = await client.post(
        f"/events/{create_event_from_event_creator}/members",
        json=jsonable_encoder(request),
        headers=create_headers(create_event_creator["id"]),
    )
    assert response.status_code == 201
    assert response.json() == create_user["id"]


async def test_creator_cant_add_not_user(client, create_event_creator, create_event_from_event_creator, create_user):
    request = MemberRequestSchema(email="notexistsmail@mail.com", role=EventRole.CHAIR)
    response = await client.post(
        f"/events/{create_event_from_event_creator}/members",
        json=jsonable_encoder(request),
        headers=create_headers(create_event_creator["id"]),
    )
    assert response.status_code == 404
    assert response.json()["detail"]["errorcode"] == "USER_NOT_FOUND"


async def test_creator_can_not_add_user_as_chair_twice_member_already_exists(
    client, create_event_creator, create_event_from_event_creator, create_user
):
    request = MemberRequestSchema(email=create_user["email"], role=EventRole.CHAIR)
    response = await client.post(
        f"/events/{create_event_from_event_creator}/members",
        json=jsonable_encoder(request),
        headers=create_headers(create_event_creator["id"]),
    )
    assert response.status_code == 201
    assert response.json() == create_user["id"]

    response = await client.post(
        f"/events/{create_event_from_event_creator}/members",
        json=jsonable_encoder(request),
        headers=create_headers(create_event_creator["id"]),
    )
    assert response.status_code == 409
    assert response.json()["detail"]["errorcode"] == "ALREADY_MEMBER_EXIST"


async def test_organizer_can_add_user_as_chair(client, create_organizer, create_event_from_event_creator, create_user):
    request = MemberRequestSchema(email=create_user["email"], role=EventRole.CHAIR)
    response = await client.post(
        f"events/{create_event_from_event_creator}/members",
        json=jsonable_encoder(request),
        headers=create_headers(create_organizer),
    )
    assert response.status_code == 201
    assert response.json() == create_user["id"]


async def test_add_tracks_that_exist_in_the_event_success(
    client, create_event_creator, create_event_from_event_creator, create_event_chair
):
    add_tracks_request = DynamicTracksEventSchema(
        tracks=["math"],
    )
    response = await client.put(
        f"/events/{create_event_from_event_creator}/chairs/{create_event_chair}/tracks",
        json=jsonable_encoder(add_tracks_request),
        headers=create_headers(create_event_creator["id"]),
    )
    assert response.status_code == 204


async def test_add_tracks_that_dont_exists_in_event_raises_error(
    client, create_event_creator, create_event_from_event_creator, create_event_chair
):
    add_tracks_request = DynamicTracksEventSchema(
        tracks=["futbol", "tenis"],
    )
    response = await client.put(
        f"/events/{create_event_from_event_creator}/chairs/{create_event_chair}/tracks",
        json=jsonable_encoder(add_tracks_request),
        headers=create_headers(create_event_creator["id"]),
    )
    assert response.status_code == 409


async def test_add_tracks_to_member_that_is_not_chair_fails(
    client, create_event_creator, create_event_from_event_creator, create_user
):
    add_tracks_request = DynamicTracksEventSchema(
        tracks=["First Track"],
    )
    response = await client.put(
        f"/events/{create_event_from_event_creator}/chairs/{create_user['id']}/tracks",
        json=jsonable_encoder(add_tracks_request),
        headers=create_headers(create_event_creator["id"]),
    )
    assert response.status_code == 404
    assert response.json()["detail"] == UserNotIsChair(create_event_from_event_creator, create_user["id"]).detail


async def test_change_tracks_to_new_tracks_the_tracks_are_fully_updated(
    client, create_event_creator, create_event_from_event_creator, create_event_chair
):
    add_tracks_request = DynamicTracksEventSchema(
        tracks=["math"],
    )
    response = await client.put(
        f"/events/{create_event_from_event_creator}/chairs/{create_event_chair}/tracks",
        json=jsonable_encoder(add_tracks_request),
        headers=create_headers(create_event_creator["id"]),
    )
    assert response.status_code == 204
    add_tracks_request.tracks = ["chemistry"]
    response = await client.put(
        f"/events/{create_event_from_event_creator}/chairs/{create_event_chair}/tracks",
        json=jsonable_encoder(add_tracks_request),
        headers=create_headers(create_event_creator["id"]),
    )
    assert response.status_code == 204
    response = await client.get(
        f"/events/{create_event_from_event_creator}/chairs/{create_event_chair}",
        headers=create_headers(create_event_creator["id"]),
    )
    assert response.status_code == 200
    assert len(response.json()["tracks"]) == 1
    assert response.json()["tracks"][0] == "chemistry"


async def test_remove_all_chair_tracks_by_setting_the_list_to_empty(
    client, create_event_creator, create_event_from_event_creator, create_event_chair
):
    add_tracks_request = DynamicTracksEventSchema(
        tracks=["math"],
    )
    response = await client.put(
        f"/events/{create_event_from_event_creator}/chairs/{create_event_chair}/tracks",
        json=jsonable_encoder(add_tracks_request),
        headers=create_headers(create_event_creator["id"]),
    )
    assert response.status_code == 204
    add_tracks_request.tracks = []
    response = await client.put(
        f"/events/{create_event_from_event_creator}/chairs/{create_event_chair}/tracks",
        json=jsonable_encoder(add_tracks_request),
        headers=create_headers(create_event_creator["id"]),
    )
    assert response.status_code == 204
    response = await client.get(
        f"/events/{create_event_from_event_creator}/chairs/{create_event_chair}",
        headers=create_headers(create_event_creator["id"]),
    )
    assert response.status_code == 200
    assert len(response.json()["tracks"]) == 0


async def test_can_delete_a_chair(client, create_event_creator, create_event_from_event_creator, create_event_chair):
    response = await client.delete(
        f"/events/{create_event_from_event_creator}/chairs/{create_event_chair}",
        headers=create_headers(create_event_creator["id"]),
    )
    assert response.status_code == 204
