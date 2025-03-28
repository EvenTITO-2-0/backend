import pytest
from fastapi.encoders import jsonable_encoder

from app.schemas.events.roles import EventRole
from app.schemas.members.member_schema import MemberRequestSchema
from app.schemas.users.user import UserSchema

from ...commontest import create_headers


@pytest.fixture(scope="function")
async def create_organizer(client, create_event_creator, create_event_from_event_creator):
    organizer = UserSchema(name="Martina", lastname="Rodriguez", email="mrodriguez@email.com")
    organizer_id = "frlasdvpqqad08jd123456789223"
    await client.post("/users", json=jsonable_encoder(organizer), headers=create_headers(organizer_id))
    request = MemberRequestSchema(email=organizer.email, role=EventRole.ORGANIZER)
    response = await client.post(
        f"/events/{create_event_from_event_creator}/members",
        json=jsonable_encoder(request),
        headers=create_headers(create_event_creator["id"]),
    )

    assert response.status_code == 201
    return organizer_id
