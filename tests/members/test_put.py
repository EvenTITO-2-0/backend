from fastapi.encoders import jsonable_encoder

from app.schemas.events.roles import EventRole
from app.schemas.members.member_schema import RolesRequestSchema

from ..commontest import create_headers


async def test_put_event_member_add_chair_role(
    client, create_event_chair, create_event_creator, create_event_from_event_creator
):
    request = RolesRequestSchema(roles=[EventRole.CHAIR, EventRole.ORGANIZER])
    response = await client.put(
        f"/events/{create_event_from_event_creator}/members/{create_event_chair}/roles",
        json=jsonable_encoder(request),
        headers=create_headers(create_event_creator["id"]),
    )
    assert response.status_code == 204, f"error: {response.json()}"
