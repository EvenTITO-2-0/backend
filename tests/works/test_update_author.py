from fastapi.encoders import jsonable_encoder

from app.database.models.inscription import InscriptionRole
from app.schemas.inscriptions.inscription import InscriptionRequestSchema

from ..commontest import create_headers
from .test_create_work import USER_WORK


async def test_get_work_author_can_update_his_work(client, create_user, create_event_started):
    new_inscription = InscriptionRequestSchema(roles=[InscriptionRole.SPEAKER])

    response = await client.post(
        f"/events/{create_event_started}/inscriptions",
        headers=create_headers(create_user["id"]),
        json=jsonable_encoder(new_inscription),
    )
    assert response.status_code == 201
    response = await client.post(
        f"/events/{create_event_started}/works",
        json=jsonable_encoder(USER_WORK),
        headers=create_headers(create_user["id"]),
    )
    work_id = response.json()
    update_work = USER_WORK.model_copy()
    update_work.title = "new work title"

    response = await client.put(
        f"/events/{create_event_started}/works/{work_id}",
        json=jsonable_encoder(update_work),
        headers=create_headers(create_user["id"]),
    )

    assert response.status_code == 204

    work_response = await client.get(
        f"/events/{create_event_started}/works/{work_id}", headers=create_headers(create_user["id"])
    )
    work_get = work_response.json()
    assert work_response.status_code == 200

    assert work_get["title"] == update_work.title
