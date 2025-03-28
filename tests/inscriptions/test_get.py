from fastapi.encoders import jsonable_encoder

from app.database.models.inscription import InscriptionStatus
from app.database.models.payment import PaymentStatus
from app.schemas.inscriptions.inscription import InscriptionRequestSchema
from app.schemas.payments.payment import PaymentRequestSchema

from ..commontest import create_headers
from ..works.test_create_work import USER_WORK


async def test_get_inscriptions(client, create_inscription, admin_data):
    event_id = create_inscription["event_id"]
    response = await client.get(f"/events/{event_id}/inscriptions", headers=create_headers(admin_data.id))

    assert response.status_code == 200
    inscriptions = response.json()
    assert len(inscriptions) == 1
    inscription = inscriptions[0]
    assert inscription["user_id"] == create_inscription["user_id"]
    assert inscription["id"] == create_inscription["id"]
    assert inscription["user"]["fullname"] == "Lio Messi"
    assert inscription["user"]["email"] == "lio_messi@email.com"
    assert inscription["event_id"] == event_id
    assert inscription["status"] == InscriptionStatus.PENDING_APPROVAL
    assert inscription["roles"][0] == "ATTENDEE"
    assert inscription["affiliation"] == "Fiuba"


async def test_user_inscribes_to_two_events(client, create_user, create_many_events_started):
    new_inscription = InscriptionRequestSchema(
        roles=["ATTENDEE"],
        affiliation="Fiuba",
    )
    _ = await client.post(
        f"/events/{create_many_events_started[0]}/inscriptions",
        json=jsonable_encoder(new_inscription),
        headers=create_headers(create_user["id"]),
    )

    _ = await client.post(
        f"/events/{create_many_events_started[1]}/inscriptions",
        json=jsonable_encoder(new_inscription),
        headers=create_headers(create_user["id"]),
    )

    response = await client.get("/events/my-events", headers=create_headers(create_user["id"]))

    assert response.status_code == 200

    inscriptions_response = response.json()
    inscripted_events = [create_many_events_started[0], create_many_events_started[1]]
    assert len(inscriptions_response) == 2
    for inscription in inscriptions_response:
        assert inscription["id"] in inscripted_events


async def test_get_inscription(client, create_user, create_event_started, create_speaker_inscription):
    inscription_id = create_speaker_inscription["id"]
    response = await client.get(
        f"/events/{create_event_started}/inscriptions/{inscription_id}", headers=create_headers(create_user["id"])
    )

    assert response.status_code == 200
    inscription = response.json()
    assert inscription["id"] == inscription_id
    assert inscription["user_id"] == create_user["id"]
    assert inscription["user"]["fullname"] == "Lio Messi"
    assert inscription["user"]["email"] == "lio_messi@email.com"
    assert inscription["event_id"] == create_event_started
    assert inscription["status"] == InscriptionStatus.PENDING_APPROVAL
    assert inscription["roles"][0] == "SPEAKER"
    assert inscription["affiliation"] == "Fiuba"


async def test_get_affiliation(client, create_user, create_event_started, create_speaker_inscription):
    inscription_id = create_speaker_inscription["id"]
    response = await client.get(
        f"/events/{create_event_started}/inscriptions/{inscription_id}/affiliation",
        headers=create_headers(create_user["id"]),
    )

    assert response.status_code == 200
    inscription = response.json()
    assert inscription["id"] == inscription_id
    assert inscription["download_url"]["download_url"] == "mocked-url-download"


async def test_get_payment_url(
    client, create_user, create_event_started, create_work_from_user, create_speaker_inscription
):
    inscription_id = create_speaker_inscription["id"]
    pay_inscription = PaymentRequestSchema(
        fare_name="tarifa a pagar",
        works=[create_work_from_user],
    )

    response = await client.put(
        f"/events/{create_event_started}/inscriptions/{inscription_id}/pay",
        headers=create_headers(create_user["id"]),
        json=jsonable_encoder(pay_inscription),
    )
    assert response.status_code == 201
    payment_id_1 = response.json()["id"]

    response = await client.get(
        f"/events/{create_event_started}/inscriptions/{inscription_id}/payments/{payment_id_1}",
        headers=create_headers(create_user["id"]),
    )

    assert response.status_code == 200
    payment = response.json()
    assert payment["id"] == payment_id_1
    assert payment["event_id"] == create_event_started
    assert payment["inscription_id"] == inscription_id
    assert payment["status"] == PaymentStatus.PENDING_APPROVAL
    assert len(payment["works"]) == 1
    assert payment["works"][0]["id"] == create_work_from_user
    assert payment["works"][0]["track"] == "chemistry"
    assert payment["works"][0]["title"] == USER_WORK.title
    assert payment["fare_name"] == "tarifa a pagar"
    assert payment["download_url"]["download_url"] == "mocked-url-download"
