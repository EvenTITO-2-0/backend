from fastapi.encoders import jsonable_encoder

from app.database.models.inscription import InscriptionRole
from app.schemas.inscriptions.inscription import InscriptionRequestSchema
from app.schemas.works.author import AuthorInformation
from app.schemas.works.work import CreateWorkSchema

from ..commontest import create_headers

USER_WORK = CreateWorkSchema(
    title=(
        "Comparación del Rendimiento de Curve25519, "
        "P-256 y Curvas de Edwards en Algoritmos "
        "de Criptografía Cuántica"
    ),
    track="chemistry",
    abstract="",
    keywords=["ciber", "security"],
    authors=[AuthorInformation(full_name="Mateo Perez", membership="fiuba", mail="mail@mail.com", is_speaker=False)],
)


async def test_create_work(client, create_user, create_event_started):
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
    assert response.status_code == 201


async def test_create_work_without_inscription(client, create_user, create_event):
    event_id = create_event["id"]
    response = await client.post(
        f"/events/{event_id}/works", json=jsonable_encoder(USER_WORK), headers=create_headers(create_user["id"])
    )
    assert response.status_code == 404, "Cannot create work if you dont have speaker inscription"


async def test_create_two_works_same_title_same_event_fails(client, create_user, create_event_started):
    """
    When many works are created in the same event, they all should have a different incremental id.
    """

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

    second_response = await client.post(
        f"/events/{create_event_started}/works",
        json=jsonable_encoder(USER_WORK),
        headers=create_headers(create_user["id"]),
    )

    assert response.status_code == 201
    assert second_response.status_code == 409, "The second response should fail given that the title is repeated"


async def test_create_work_without_membership(client, create_user, create_event_started):
    new_inscription = InscriptionRequestSchema(roles=[InscriptionRole.SPEAKER])

    response = await client.post(
        f"/events/{create_event_started}/inscriptions",
        headers=create_headers(create_user["id"]),
        json=jsonable_encoder(new_inscription),
    )
    assert response.status_code == 201

    new_work = CreateWorkSchema(
        title="titulo",
        track="chemistry",
        abstract="lalalala",
        keywords=["ciber", "security"],
        authors=[AuthorInformation(full_name="Mateo Perez", mail="mail@mail.com", is_speaker=False)],
    )
    response = await client.post(
        f"/events/{create_event_started}/works",
        json=jsonable_encoder(new_work),
        headers=create_headers(create_user["id"]),
    )
    assert response.status_code == 201
