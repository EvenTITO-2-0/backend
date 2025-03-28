import pytest
from fastapi.encoders import jsonable_encoder

from app.database.models.event import EventStatus
from app.database.models.inscription import InscriptionRole
from app.schemas.events.event_status import EventStatusSchema
from app.schemas.inscriptions.inscription import InscriptionRequestSchema

from ...commontest import create_headers


@pytest.fixture(scope="function")
async def create_inscription(client, create_user, create_event_started):
    new_inscription = InscriptionRequestSchema(
        roles=["ATTENDEE"],
        affiliation="Fiuba",
    )

    response = await client.post(
        f"/events/{create_event_started}/inscriptions",
        json=jsonable_encoder(new_inscription),
        headers=create_headers(create_user["id"]),
    )
    return {"id": response.json()["id"], "event_id": create_event_started, "user_id": create_user["id"]}


@pytest.fixture(scope="function")
async def create_speaker_inscription(client, create_user, create_event_started):
    new_inscription = InscriptionRequestSchema(
        roles=["SPEAKER"],
        affiliation="Fiuba",
    )

    response = await client.post(
        f"/events/{create_event_started}/inscriptions",
        json=jsonable_encoder(new_inscription),
        headers=create_headers(create_user["id"]),
    )
    return {"id": response.json()["id"], "event_id": create_event_started, "user_id": create_user["id"]}


@pytest.fixture(scope="function")
async def create_event_started_with_inscription_from_event_creator(
    admin_data, client, create_event_creator, create_event_from_event_creator
):
    status_update = EventStatusSchema(status=EventStatus.STARTED)

    await client.patch(
        f"/events/{create_event_from_event_creator}/status",
        json=jsonable_encoder(status_update),
        headers=create_headers(admin_data.id),
    )
    new_inscription = InscriptionRequestSchema(roles=[InscriptionRole.SPEAKER])

    response = await client.post(
        f"/events/{create_event_from_event_creator}/inscriptions",
        headers=create_headers(create_event_creator["id"]),
        json=jsonable_encoder(new_inscription),
    )
    assert response.status_code == 201, response.json()
