from fastapi.encoders import jsonable_encoder

from app.database.models.work import WorkStates
from app.schemas.works.talk import Talk
from app.schemas.works.work import WorkUpdateAdministrationSchema

from ..commontest import create_headers
from .test_create_work import USER_WORK


async def test_put_event_from_organizer(
    client, create_user, create_work_from_user, create_event_started, admin_data, create_speaker_inscription
):
    work_response = await client.get(
        f"/events/{create_event_started}/works/{create_work_from_user}", headers=create_headers(create_user["id"])
    )

    assert work_response.status_code == 200
    work_get = work_response.json()

    assert work_get["talk"] is None
    assert work_get["track"] == "chemistry"

    update = WorkUpdateAdministrationSchema(
        talk=Talk(date="2024-01-01 09:00:00", location="FIUBA, Av. Paseo Colon 850", duration=60), track="math"
    )
    response = await client.put(
        f"/events/{create_event_started}/works/{create_work_from_user}/administration",
        json=jsonable_encoder(update),
        headers=create_headers(admin_data.id),
    )
    assert response.status_code == 204

    work_response = await client.get(
        f"/events/{create_event_started}/works/{create_work_from_user}", headers=create_headers(create_user["id"])
    )

    assert work_response.status_code == 200
    work_get = work_response.json()

    assert work_get["title"] == USER_WORK.title
    assert work_get["id"] == create_work_from_user
    assert work_get["state"] == WorkStates.SUBMITTED
    assert len(work_get["authors"]) == len(USER_WORK.authors)
    assert work_get["authors"][0]["membership"] == USER_WORK.authors[0].membership
    assert len(work_get["keywords"]) == len(USER_WORK.keywords)
    assert work_get["keywords"][0] == USER_WORK.keywords[0]
    assert work_get["abstract"] == USER_WORK.abstract
    assert work_get["track"] == "math"
    assert work_get["talk"]["location"] == "FIUBA, Av. Paseo Colon 850"
    assert work_get["talk"]["date"] == "2024-01-01T09:00:00"
    assert work_get["talk"]["duration"] == 60
