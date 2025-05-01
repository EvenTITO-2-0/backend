from fastapi.encoders import jsonable_encoder

from app.schemas.events.roles import EventRole
from app.schemas.members.member_schema import MemberRequestSchema
from tests.commontest import create_headers


async def test_event_creator_can_remove_other_organizer(
    client, create_organizer, create_event_from_event_creator, create_event_creator
):
    response = await client.delete(
        f"/events/{create_event_from_event_creator}" f"/organizers/{create_organizer}",
        headers=create_headers(create_event_creator["id"]),
    )
    assert response.status_code == 201


async def test_event_organizer_can_remove_other_event_organizer(
    client, create_organizer, create_event_creator, create_event_from_event_creator, create_user
):
    request = MemberRequestSchema(
        email=create_user["email"],
        role=EventRole.ORGANIZER,
    )
    await client.post(
        f"/events/{create_event_from_event_creator}/members",
        json=jsonable_encoder(request),
        headers=create_headers(create_event_creator["id"]),
    )

    response = await client.delete(
        f"/events/{create_event_from_event_creator}" f"/organizers/{create_user['id']}",
        headers=create_headers(create_organizer),
    )
    assert response.status_code == 201


async def test_simple_user_tries_remove_organizer_fails(
    client, create_organizer, create_event_from_event_creator, create_user
):
    response = await client.delete(
        f"/events/{create_event_from_event_creator}" f"/organizers/{create_organizer}",
        headers=create_headers(create_user["id"]),
    )

    assert response.status_code == 403
