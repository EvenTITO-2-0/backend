import pytest
from fastapi.encoders import jsonable_encoder

from app.schemas.events.roles import EventRole
from app.schemas.members.member_schema import MemberRequestSchema
from tests.commontest import create_headers


@pytest.fixture(scope="function")
async def create_event_chair(client, create_user, create_event_creator, create_event_from_event_creator):
    create_member_request = MemberRequestSchema(email=create_user["email"], role=EventRole.CHAIR)
    response = await client.post(
        f"/events/{create_event_from_event_creator}/members",
        json=jsonable_encoder(create_member_request),
        headers=create_headers(create_event_creator["id"]),
    )
    assert response.status_code == 201
    return create_user["id"]
