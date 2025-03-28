import datetime

from fastapi.encoders import jsonable_encoder

from app.schemas.events.configuration_general import ConfigurationGeneralEventSchema
from app.schemas.events.dates import DateSchema, DatesCompleteSchema, MandatoryDates
from app.schemas.events.schemas import DynamicTracksEventSchema
from tests.commontest import create_headers


async def add_notification_mails(client, event_id, creator_user_id):
    event = ConfigurationGeneralEventSchema()
    event.notification_mails = ["eventito_test@hotmail.com"]
    event.contact = "Pepe"
    event.organized_by = "Jose"
    event.dates[0].date = "2024-09-02"
    event.dates[0].time = "15:30:00"

    response = await client.put(
        f"/events/{event_id}/configuration/general",
        json=jsonable_encoder(event),
        headers=create_headers(creator_user_id),
    )

    assert response.status_code == 204


async def add_tracks(client, event_id, creator_user_id):
    tracks_to_add = DynamicTracksEventSchema(tracks=["math", "chemistry", "physics"])
    response = await client.put(
        f"/events/{event_id}/configuration/general/tracks",
        json=jsonable_encoder(tracks_to_add),
        headers=create_headers(creator_user_id),
    )
    assert response.status_code == 204


async def add_dates(client, event_id, creator_user_id):
    dates = DatesCompleteSchema(
        dates=[
            DateSchema(
                name=MandatoryDates.START_DATE,
                label="Fecha de Comienzo",
                description="Fecha de comienzo del evento.",
                is_mandatory=True,
                date=datetime.date.today() + datetime.timedelta(days=31),
                time=datetime.time(15, 30),
            ),
            DateSchema(
                name=MandatoryDates.END_DATE,
                label="Fecha de Finalización",
                description="Fecha de Finalización del evento.",
                is_mandatory=True,
                date=datetime.date.today() + datetime.timedelta(days=32),
                time=datetime.time(15, 30),
            ),
            DateSchema(
                name=MandatoryDates.SUBMISSION_DEADLINE_DATE,
                label="Fecha de envío de trabajos",
                description="Fecha límite de envío de trabajos.",
                is_mandatory=True,
                date=datetime.date.today() + datetime.timedelta(days=30),
                time=datetime.time(15, 30),
            ),
        ]
    )

    response = await client.put(
        f"/events/{event_id}/configuration/dates", json=jsonable_encoder(dates), headers=create_headers(creator_user_id)
    )
    assert response.status_code == 204


async def complete_event_configuration(client, event_id, creator_user_id):
    await add_dates(client, event_id, creator_user_id)
    await add_tracks(client, event_id, creator_user_id)
