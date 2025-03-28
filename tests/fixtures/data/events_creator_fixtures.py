import pytest
from fastapi.encoders import jsonable_encoder

from app.database.models.event import EventStatus, EventType
from app.database.models.user import UserRole
from app.schemas.events.create_event import CreateEventSchema
from app.schemas.events.event_status import EventStatusSchema
from app.schemas.users.user import UserSchema
from app.schemas.users.user_role import UserRoleSchema

from ...commontest import create_headers, get_user_method
from .helper import complete_event_configuration


@pytest.fixture(scope="function")
async def create_event_creator(client, admin_data):
    event_creator = UserSchema(
        name="Juan",
        lastname="Martinez",
        email="jmartinez@email.com",
    )
    user_id = await client.post(
        "/users", json=jsonable_encoder(event_creator), headers=create_headers("lakjsdeuimx213klasmd31234567")
    )
    user_id = user_id.json()
    new_role = UserRoleSchema(role=UserRole.EVENT_CREATOR.value)
    _ = await client.patch(
        f"/users/{user_id}/roles", json=jsonable_encoder(new_role), headers=create_headers(admin_data.id)
    )

    event_creator_user = await get_user_method(client, user_id)
    return event_creator_user


@pytest.fixture(scope="function")
async def create_event_from_event_creator(client, create_event_creator):
    new_event = CreateEventSchema(
        title="Event Creator Event",
        start_date="2024-09-02",
        end_date="2024-09-04",
        description="This is a nice event",
        event_type=EventType.CONFERENCE,
        location="Paseo Colon 850",
    )
    response = await client.post(
        "/events", json=jsonable_encoder(new_event), headers=create_headers(create_event_creator["id"])
    )
    assert response.status_code == 201

    event_id = response.json()

    await complete_event_configuration(client, event_id, create_event_creator["id"])

    return event_id


@pytest.fixture(scope="function")
async def create_event_started_from_event_creator(
    admin_data, client, create_event_creator, create_event_from_event_creator
):
    status_update = EventStatusSchema(status=EventStatus.STARTED)

    response = await client.patch(
        f"/events/{create_event_from_event_creator}/status",
        json=jsonable_encoder(status_update),
        headers=create_headers(admin_data.id),
    )

    assert response.status_code == 204, response.json()
    return create_event_from_event_creator
