from fastapi.encoders import jsonable_encoder

from app.schemas.events.roles import EventRole
from app.schemas.members.member_schema import MemberRequestSchema

from ..commontest import create_headers


async def add_organizer(client, event_id, user_id, email):
    request = MemberRequestSchema(email=email, role=EventRole.ORGANIZER)
    return await client.post(
        f"/events/{event_id}/organizers", json=jsonable_encoder(request), headers=create_headers(user_id)
    )
