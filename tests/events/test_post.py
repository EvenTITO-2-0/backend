import datetime

from fastapi.encoders import jsonable_encoder

from app.database.models.event import EventStatus, EventType
from app.exceptions.events_exceptions import InvalidEventSameTitle
from app.schemas.events.create_event import CreateEventSchema
from app.schemas.events.dates import DateSchema, MandatoryDates

from ..commontest import create_headers


async def test_post_event(client, admin_data):
    new_event = CreateEventSchema(
        title="Event Title",
        description="This is a nice event",
        event_type=EventType.CONFERENCE,
        location="Paseo Colon 850",
        tracks=["math", "chemistry", "phisics"],
    )
    response = await client.post("/events", json=jsonable_encoder(new_event), headers=create_headers(admin_data.id))
    assert response.status_code == 201

    response_data = response.json()
    assert response_data is not None


async def test_post_event_with_event_creator_the_event_is_created(client, create_event_creator):
    new_event = CreateEventSchema(
        title="Event Title",
        description="This is a nice event",
        event_type=EventType.CONFERENCE,
        location="Paseo Colon 850",
        tracks=["math", "chemistry", "phisics"],
    )
    response = await client.post(
        "/events", json=jsonable_encoder(new_event), headers=create_headers(create_event_creator["id"])
    )
    assert response.status_code == 201
    event_id = response.json()

    response = await client.get(f"/events/{event_id}/public", headers=create_headers(create_event_creator["id"]))
    assert response.json()["status"] == EventStatus.CREATED


async def test_post_event_invaluser_id(client):
    event = CreateEventSchema(
        title="Another Event Title",
        description="This is a nice event",
        event_type=EventType.CONFERENCE,
        location="Paseo Colon 850",
        tracks=["math", "chemistry", "phisics"],
    )

    response = await client.post(
        "/events", json=jsonable_encoder(event), headers=create_headers("invalidcreatorid123456789098")
    )

    assert response.status_code == 404


async def test_post_event_same_without_optional_args(client, admin_data):
    json = jsonable_encoder(
        {
            "title": "Event Title",
            "description": "This is a nice event",
            "event_type": EventType.CONFERENCE,
        }
    )
    response = await client.post("/events", json=json, headers=create_headers(admin_data.id))
    assert response.status_code == 201


async def test_post_event_start_date_gt_end_date_fails(client, admin_data):
    today = datetime.date.today()
    json = jsonable_encoder(
        {
            "title": "Event Title",
            "description": "This is a nice event",
            "dates": [
                DateSchema(
                    name=MandatoryDates.START_DATE,
                    label="Fecha de Comienzo",
                    description="Fecha de comienzo del evento.",
                    is_mandatory=True,
                    date=today + datetime.timedelta(days=31),
                ).model_dump(mode="json"),
                DateSchema(
                    name=MandatoryDates.END_DATE,
                    label="Fecha de Finalización",
                    description="Fecha de comienzo del evento.",
                    is_mandatory=True,
                    date=today + datetime.timedelta(days=30),
                ).model_dump(mode="json"),
                DateSchema(
                    name=MandatoryDates.SUBMISSION_DEADLINE_DATE,
                    label="Fecha de envío de trabajos",
                    description="Fecha límite de envío de trabajos.",
                    is_mandatory=True,
                ).model_dump(mode="json"),
            ],
            "event_type": EventType.CONFERENCE,
            "location": "Paseo Colon 850",
            "tracks": ["math, chemistry, phisics"],
        }
    )
    response = await client.post("/events", json=json, headers=create_headers(admin_data.id))
    assert response.status_code == 422


async def test_post_event_with_dates(client, admin_data):
    today = datetime.date.today()
    json = jsonable_encoder(
        {
            "title": "Event Title",
            "description": "This is a nice event",
            "dates": [
                DateSchema(
                    name=MandatoryDates.START_DATE,
                    label="Fecha de Comienzo",
                    description="Fecha de comienzo del evento.",
                    is_mandatory=True,
                    date=today + datetime.timedelta(days=20),
                ).model_dump(mode="json"),
                DateSchema(
                    name=MandatoryDates.END_DATE,
                    label="Fecha de Finalización",
                    description="Fecha de comienzo del evento.",
                    is_mandatory=True,
                    date=today + datetime.timedelta(days=30),
                ).model_dump(mode="json"),
                DateSchema(
                    name=MandatoryDates.SUBMISSION_DEADLINE_DATE,
                    label="Fecha de envío de trabajos",
                    description="Fecha límite de envío de trabajos.",
                    is_mandatory=True,
                ).model_dump(mode="json"),
            ],
            "event_type": EventType.CONFERENCE,
            "location": "Paseo Colon 850",
            "tracks": ["math, chemistry, phisics"],
        }
    )
    response = await client.post("/events", json=json, headers=create_headers(admin_data.id))
    assert response.status_code == 201


async def test_post_event_same_title_fails(client, create_event, create_user, admin_data):
    response = await client.get(f"/events/{create_event['id']}/public", headers=create_headers(create_user["id"]))
    assert response.status_code == 200
    title = response.json()["title"]

    new_event = CreateEventSchema(
        title=title,
        description="This is a nice event",
        event_type=EventType.CONFERENCE,
        location="Paseo Colon 850",
        tracks=["math", "chemistry", "phisics"],
    )
    response = await client.post("/events", json=jsonable_encoder(new_event), headers=create_headers(admin_data.id))
    assert response.status_code == 409
    assert response.json()["detail"] == InvalidEventSameTitle(title).detail
