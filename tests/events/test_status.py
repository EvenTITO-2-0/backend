from fastapi.encoders import jsonable_encoder

from app.database.models.event import EventStatus, EventType
from app.schemas.events.create_event import CreateEventSchema
from app.schemas.events.event_status import EventStatusSchema

from ..commontest import create_headers


async def test_event_created_by_user_has_waiting_approved_status(client, create_user):
    new_event = CreateEventSchema(
        title="Event Title",
        start_date="2024-09-02",
        end_date="2024-09-04",
        description="This is a nice event",
        event_type=EventType.CONFERENCE,
        location="Paseo Colon 850",
        tracks=["math", "chemistry", "phisics"],
    )
    event_id = await client.post("/events", json=jsonable_encoder(new_event), headers=create_headers(create_user["id"]))
    event_id = event_id.json()
    response = await client.get(f"/events/{event_id}/public", headers=create_headers(create_user["id"]))
    assert response.json()["status"] == EventStatus.WAITING_APPROVAL


async def test_event_created_organizer_cant_change_status(client, create_event, create_user):
    status_update = EventStatusSchema(status=EventStatus.CREATED)
    response = await client.patch(
        f"/events/{create_event['id']}/status",
        json=jsonable_encoder(status_update),
        headers=create_headers(create_user["id"]),
    )

    assert response.status_code == 403


async def test_organizer_can_change_status_to_started_after_created(
    client, create_event_from_event_creator, create_organizer, admin_data
):
    status_update = EventStatusSchema(status=EventStatus.CREATED)
    response = await client.patch(
        f"/events/{create_event_from_event_creator}/status",
        json=jsonable_encoder(status_update),
        headers=create_headers(admin_data.id),
    )

    assert response.status_code == 204
    status_update = EventStatusSchema(status=EventStatus.STARTED)
    response = await client.patch(
        f"/events/{create_event_from_event_creator}/status",
        json=jsonable_encoder(status_update),
        headers=create_headers(create_organizer),
    )

    assert response.status_code == 204


async def test_event_created_admin_can_change_status(client, create_event, admin_data):
    status_update = EventStatusSchema(status=EventStatus.CREATED)
    response = await client.patch(
        f"/events/{create_event['id']}/status",
        json=jsonable_encoder(status_update),
        headers=create_headers(admin_data.id),
    )
    assert response.status_code == 204
    response = await client.get(f"/events/{create_event['id']}/public", headers=create_headers(admin_data.id))
    assert response.json()["status"] == status_update.status
