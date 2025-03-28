import datetime

from fastapi.encoders import jsonable_encoder

from app.database.models.event import EventStatus
from app.database.models.inscription import InscriptionRole
from app.schemas.events.event_status import EventStatusSchema
from app.schemas.events.roles import EventRole
from app.schemas.inscriptions.inscription import InscriptionRequestSchema
from app.schemas.members.member_schema import MemberRequestSchema
from app.schemas.members.reviewer_schema import ReviewerCreateRequestSchema, ReviewerRequestSchema

from ..commontest import create_headers
from ..works.test_create_work import USER_WORK


async def test_get_members_ok(admin_data, client, create_user, create_event_creator, create_event_from_event_creator):
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

    create_work_response = await client.post(
        f"/events/{create_event_from_event_creator}/works",
        json=jsonable_encoder(USER_WORK),
        headers=create_headers(create_event_creator["id"]),
    )
    assert create_work_response.status_code == 201, create_work_response.json()

    work_id = create_work_response.json()

    # agregar reviewers
    new_reviewer_1 = ReviewerRequestSchema(
        work_id=work_id, email=create_user["email"], review_deadline=datetime.date.today() + datetime.timedelta(days=10)
    )
    new_reviewer_2 = ReviewerRequestSchema(
        work_id=work_id,
        email=create_event_creator["email"],
        review_deadline=datetime.date.today() + datetime.timedelta(days=10),
    )

    request = ReviewerCreateRequestSchema(reviewers=[new_reviewer_1, new_reviewer_2])

    response = await client.post(
        f"/events/{create_event_from_event_creator}/reviewers",
        json=jsonable_encoder(request),
        headers=create_headers(create_event_creator["id"]),
    )

    assert response.status_code == 201

    # agregar chair
    create_member_request = MemberRequestSchema(email=create_user["email"], role=EventRole.CHAIR)
    response = await client.post(
        f"/events/{create_event_from_event_creator}/members",
        json=jsonable_encoder(create_member_request),
        headers=create_headers(create_event_creator["id"]),
    )

    assert response.status_code == 201

    get_response = await client.get(
        f"/events/{create_event_from_event_creator}/members", headers=create_headers(create_event_creator["id"])
    )

    assert get_response.status_code == 200

    member_list = get_response.json()
    assert len(member_list[0]["roles"]) == 1  # Only chair, reviewer is not a member.
    assert len(member_list[1]["roles"]) == 1  # Only organizer, reviewer is not a member.
    assert member_list[0]["event_id"] == create_event_from_event_creator
    assert member_list[1]["event_id"] == create_event_from_event_creator
    assert member_list[0]["user_id"] == create_user["id"]
    assert member_list[1]["user_id"] == create_event_creator["id"]
    assert set(member_list[0]["roles"]) == {"CHAIR"}
    assert set(member_list[1]["roles"]) == {"ORGANIZER"}
    assert member_list[0]["user"]["email"] == create_user["email"]
    assert member_list[1]["user"]["email"] == create_event_creator["email"]


# TODO terminar los test


async def test_get_only_one_member_organizer(
    client, create_user, create_event_creator, create_event_from_event_creator
):
    response = await client.get(
        f"/events/{create_event_from_event_creator}/members", headers=create_headers(create_event_creator["id"])
    )

    assert response.status_code == 200
    members_list = response.json()
    assert len(members_list) == 1
