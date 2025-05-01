import pytest
from fastapi.encoders import jsonable_encoder

from app.schemas.works.author import AuthorInformation
from app.schemas.works.work import CreateWorkSchema

from ...commontest import WORKS, create_headers


@pytest.fixture(scope="function")
async def create_many_works(client, create_user, create_event_started, create_speaker_inscription):
    created_works = []
    for work in WORKS:
        response = await client.post(
            f"/events/{create_event_started}/works",
            json=jsonable_encoder(work),
            headers=create_headers(create_user["id"]),
        )
        work_id = response.json()
        res = work.model_dump()
        res["id"] = work_id
        created_works.append(res)
    return created_works


@pytest.fixture(scope="function")
async def create_work_from_user(client, create_user, create_event_started, create_speaker_inscription) -> str:
    user_work = CreateWorkSchema(
        title=(
            "Comparación del Rendimiento de Curve25519, "
            "P-256 y Curvas de Edwards en Algoritmos "
            "de Criptografía Cuántica"
        ),
        track="chemistry",
        abstract="",
        keywords=["ciber", "security"],
        authors=[AuthorInformation(full_name="Mateo Perez", membership="fiuba", mail="mail@mail.com")],
    )
    response = await client.post(
        f"/events/{create_event_started}/works",
        json=jsonable_encoder(user_work),
        headers=create_headers(create_user["id"]),
    )
    assert response.status_code == 201
    return response.json()
