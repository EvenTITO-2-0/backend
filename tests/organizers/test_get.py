from fastapi.encoders import jsonable_encoder

from app.schemas.events.roles import EventRole
from app.schemas.members.member_schema import MemberRequestSchema

from ..commontest import create_headers

# TODO los test pasan pero ahora quedaron apuntando al /members porque estan en otro router, adecuar eso para que alla
# test de los routers de members (incluido lo nuevo de roles), organizers y chairs


async def test_get_organizers_with_new_organizer(
    client, create_user, create_event_creator, create_event_from_event_creator
):
    request = MemberRequestSchema(email=create_user["email"], role=EventRole.ORGANIZER)
    _ = await client.post(
        f"/events/{create_event_from_event_creator}/members",
        json=jsonable_encoder(request),
        headers=create_headers(create_event_creator["id"]),
    )

    response = await client.get(
        f"/events/{create_event_from_event_creator}/organizers", headers=create_headers(create_event_creator["id"])
    )

    assert response.status_code == 200

    organizers_list = response.json()
    assert len(organizers_list) == 2
    organizers_ids = [organizer["user_id"] for organizer in organizers_list]
    assert create_user["id"] in organizers_ids
