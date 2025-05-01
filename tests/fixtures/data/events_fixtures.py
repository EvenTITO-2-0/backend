import pytest
from fastapi.encoders import jsonable_encoder

from app.database.models.event import EventStatus, EventType
from app.schemas.events.create_event import CreateEventSchema
from app.schemas.events.event_status import EventStatusSchema

from ...commontest import EVENTS, ONE_EVENT, create_headers
from .helper import add_notification_mails, complete_event_configuration


@pytest.fixture(scope="function")
async def create_event(client, admin_data):
    new_event = CreateEventSchema(
        title="Event Title",
        start_date="2024-09-02",
        end_date="2024-09-04",
        description="This is a nice event",
        event_type=EventType.CONFERENCE,
        location="Paseo Colon 850",
        tracks=["math", "chemistry", "phisics"],
    )
    event_id = await client.post("/events", json=jsonable_encoder(new_event), headers=create_headers(admin_data.id))
    event_id = event_id.json()

    await complete_event_configuration(client, event_id, admin_data.id)

    event_dict = {**new_event.model_dump(), "id": event_id}

    return event_dict


@pytest.fixture(scope="function")
async def create_event_with_email(client, admin_data):
    new_event = CreateEventSchema(
        title="Event Title",
        start_date="2024-09-02",
        end_date="2024-09-04",
        description="This is a nice event",
        event_type=EventType.CONFERENCE,
        location="Paseo Colon 850",
        tracks=["math", "chemistry", "phisics"],
    )

    event_id = await client.post("/events", json=jsonable_encoder(new_event), headers=create_headers(admin_data.id))
    event_id = event_id.json()
    await complete_event_configuration(client, event_id, admin_data.id)
    await add_notification_mails(client, event_id, admin_data.id)

    response = await client.get(f"/events/{event_id}/configuration", headers=create_headers(admin_data.id))
    event_config = response.json()

    assert response.status_code == 200

    return event_config


@pytest.fixture(scope="function")
async def create_many_events(client, admin_data):
    ids_events = []
    for event in EVENTS:
        response = await client.post("/events", json=jsonable_encoder(event), headers=create_headers(admin_data.id))
        ids_events.append(response.json())
        await complete_event_configuration(client, response.json(), admin_data.id)

    return ids_events


@pytest.fixture(scope="function")
async def create_event_started(client, create_event, admin_data):
    status_update = EventStatusSchema(status=EventStatus.STARTED)

    await complete_event_configuration(client, create_event["id"], admin_data.id)

    await client.patch(
        f"/events/{create_event['id']}/status",
        json=jsonable_encoder(status_update),
        headers=create_headers(admin_data.id),
    )
    return create_event["id"]


@pytest.fixture(scope="function")
async def create_event_started_with_email(client, create_event, admin_data):
    status_update = EventStatusSchema(status=EventStatus.STARTED)

    await client.patch(
        f"/events/{create_event['id']}/status",
        json=jsonable_encoder(status_update),
        headers=create_headers(admin_data.id),
    )
    return create_event["id"]


@pytest.fixture(scope="function")
async def create_one_event_started(client, admin_data):
    ids_events = []
    status_update = EventStatusSchema(status=EventStatus.STARTED)

    for event in ONE_EVENT:
        response = await client.post("/events", json=jsonable_encoder(event), headers=create_headers(admin_data.id))
        event_id = response.json()

        await complete_event_configuration(client, event_id, admin_data.id)

        await client.patch(
            f"/events/{event_id}/status", json=jsonable_encoder(status_update), headers=create_headers(admin_data.id)
        )
        ids_events.append(event_id)

    return ids_events


@pytest.fixture(scope="function")
async def create_many_events_started(client, admin_data):
    ids_events = []
    status_update = EventStatusSchema(status=EventStatus.STARTED)

    for event in EVENTS:
        response = await client.post("/events", json=jsonable_encoder(event), headers=create_headers(admin_data.id))
        event_id = response.json()

        await complete_event_configuration(client, event_id, admin_data.id)

        await client.patch(
            f"/events/{event_id}/status", json=jsonable_encoder(status_update), headers=create_headers(admin_data.id)
        )
        ids_events.append(event_id)

    return ids_events
