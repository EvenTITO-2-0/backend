from fastapi.encoders import jsonable_encoder

from app.database.models.payment import PaymentStatus
from app.schemas.inscriptions.inscription import InscriptionRequestSchema
from app.schemas.payments.payment import PaymentRequestSchema, PaymentStatusSchema

from ..commontest import create_headers


async def test_get_payments(
    client, create_user, create_event_creator, create_event_started_from_event_creator, create_many_works
):
    new_inscription = InscriptionRequestSchema(
        roles=["SPEAKER"],
        affiliation="Fiuba",
    )

    response = await client.post(
        f"/events/{create_event_started_from_event_creator}/inscriptions",
        headers=create_headers(create_user["id"]),
        json=jsonable_encoder(new_inscription),
    )
    assert response.status_code == 201

    inscription_id = response.json()["id"]

    pay_inscription_1 = PaymentRequestSchema(
        fare_name="tarifa a pagar 1",
        works=[create_many_works[0]["id"]],
    )

    pay_inscription_2 = PaymentRequestSchema(
        fare_name="tarifa a pagar 2",
        works=[create_many_works[1]["id"]],
    )

    response = await client.put(
        f"/events/{create_event_started_from_event_creator}/inscriptions/{inscription_id}/pay",
        headers=create_headers(create_user["id"]),
        json=jsonable_encoder(pay_inscription_1),
    )
    assert response.status_code == 201
    payment_id_1 = response.json()["id"]
    assert payment_id_1 is not None

    response = await client.put(
        f"/events/{create_event_started_from_event_creator}/inscriptions/{inscription_id}/pay",
        headers=create_headers(create_user["id"]),
        json=jsonable_encoder(pay_inscription_2),
    )
    assert response.status_code == 201
    payment_id_2 = response.json()["id"]
    assert payment_id_2 is not None

    response = await client.get(
        f"/events/{create_event_started_from_event_creator}/payments",
        headers=create_headers(create_event_creator["id"]),
    )

    assert response.status_code == 200
    payments = response.json()
    assert len(payments) == 2

    assert payments[0]["id"] == payment_id_1
    assert payments[0]["event_id"] == create_event_started_from_event_creator
    assert payments[0]["inscription_id"] == inscription_id
    assert payments[0]["status"] == PaymentStatus.PENDING_APPROVAL
    assert len(payments[0]["works"]) == 1
    assert payments[0]["works"][0]["id"] == create_many_works[0]["id"]
    assert payments[0]["works"][0]["track"] == "chemistry"
    assert (
        payments[0]["works"][0]["title"]
        == "Comparación del Rendimiento de Curve25519, P-256 y Curvas de Edwards en Algoritmos de Criptografía "
        "Cuántica"
    )
    assert payments[0]["fare_name"] == "tarifa a pagar 1"

    assert payments[1]["id"] == payment_id_2
    assert payments[1]["event_id"] == create_event_started_from_event_creator
    assert payments[1]["inscription_id"] == inscription_id
    assert payments[1]["status"] == PaymentStatus.PENDING_APPROVAL
    assert len(payments[1]["works"]) == 1
    assert payments[1]["works"][0]["id"] == create_many_works[1]["id"]
    assert payments[1]["works"][0]["track"] == "math"
    assert (
        payments[1]["works"][0]["title"]
        == "Aplicaciones de los Toros de Clifford en la Teoría de Códigos Correctores de Errores"
    )
    assert payments[1]["fare_name"] == "tarifa a pagar 2"


async def test_patch_payments(
    client, create_user, create_event_creator, create_event_started_from_event_creator, create_many_works
):
    new_inscription = InscriptionRequestSchema(
        roles=["SPEAKER"],
        affiliation="Fiuba",
    )

    response = await client.post(
        f"/events/{create_event_started_from_event_creator}/inscriptions",
        headers=create_headers(create_user["id"]),
        json=jsonable_encoder(new_inscription),
    )
    assert response.status_code == 201

    inscription_id = response.json()["id"]

    pay_inscription_1 = PaymentRequestSchema(
        fare_name="tarifa a pagar 1",
        works=[create_many_works[0]["id"], create_many_works[1]["id"]],
    )

    pay_inscription_2 = PaymentRequestSchema(
        fare_name="tarifa a pagar 2",
        works=[create_many_works[0]["id"], create_many_works[1]["id"]],
    )

    pay_inscription_3 = PaymentRequestSchema(
        fare_name="tarifa a pagar 3",
        works=[create_many_works[0]["id"], create_many_works[1]["id"]],
    )

    response = await client.put(
        f"/events/{create_event_started_from_event_creator}/inscriptions/{inscription_id}/pay",
        headers=create_headers(create_user["id"]),
        json=jsonable_encoder(pay_inscription_1),
    )
    assert response.status_code == 201
    payment_id_1 = response.json()["id"]
    assert payment_id_1 is not None

    response = await client.put(
        f"/events/{create_event_started_from_event_creator}/inscriptions/{inscription_id}/pay",
        headers=create_headers(create_user["id"]),
        json=jsonable_encoder(pay_inscription_2),
    )
    assert response.status_code == 201
    payment_id_2 = response.json()["id"]
    assert payment_id_2 is not None

    response = await client.put(
        f"/events/{create_event_started_from_event_creator}/inscriptions/{inscription_id}/pay",
        headers=create_headers(create_user["id"]),
        json=jsonable_encoder(pay_inscription_3),
    )
    assert response.status_code == 201
    payment_id_3 = response.json()["id"]
    assert payment_id_3 is not None

    response = await client.get(
        f"/events/{create_event_started_from_event_creator}/payments",
        headers=create_headers(create_event_creator["id"]),
    )

    assert response.status_code == 200
    payments = response.json()
    assert len(payments) == 3

    assert payments[0]["status"] == PaymentStatus.PENDING_APPROVAL
    assert payments[1]["status"] == PaymentStatus.PENDING_APPROVAL
    assert payments[2]["status"] == PaymentStatus.PENDING_APPROVAL

    status_update = PaymentStatusSchema(status=PaymentStatus.APPROVED)
    response = await client.patch(
        f"/events/{create_event_started_from_event_creator}/payments/{payment_id_1}",
        json=jsonable_encoder(status_update),
        headers=create_headers(create_event_creator["id"]),
    )
    assert response.status_code == 204

    status_update = PaymentStatusSchema(status=PaymentStatus.REJECTED)
    response = await client.patch(
        f"/events/{create_event_started_from_event_creator}/payments/{payment_id_2}",
        json=jsonable_encoder(status_update),
        headers=create_headers(create_event_creator["id"]),
    )
    assert response.status_code == 204

    response = await client.get(
        f"/events/{create_event_started_from_event_creator}/payments",
        headers=create_headers(create_event_creator["id"]),
    )

    assert response.status_code == 200
    payments = response.json()
    assert len(payments) == 3

    assert payments[0]["status"] == PaymentStatus.APPROVED
    assert payments[1]["status"] == PaymentStatus.REJECTED
    assert payments[2]["status"] == PaymentStatus.PENDING_APPROVAL
