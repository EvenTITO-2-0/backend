from fastapi.encoders import jsonable_encoder

from app.schemas.events.pricing import FareSchema, PricingSchema
from app.schemas.events.roles import EventRole

from ..commontest import create_headers


async def test_put_pricing_config_ok(client, admin_data, create_event):
    students_fee = FareSchema(
        name="Students Only Fee",
        description="Only Students with certificate",
        value="50",
        currency="ARS",
        need_verification=True,
        roles=[EventRole.ATTENDEE],
    )
    pricing_config = PricingSchema(pricing=[students_fee])

    response = await client.put(
        f"/events/{create_event['id']}/configuration/pricing",
        json=jsonable_encoder(pricing_config),
        headers=create_headers(admin_data.id),
    )
    assert response.status_code == 204

    response = await client.get(f"/events/{create_event['id']}/public", headers=create_headers(admin_data.id))

    assert response.status_code == 200
    assert response.json()["pricing"][0]["name"] == students_fee.name


async def test_put_pricing_with_related_data_ok(client, admin_data, create_event):
    students_fee_attendee = FareSchema(
        name="Attendee students Only Fee",
        description="Only Students with certificate",
        value="50",
        currency="ARS",
        need_verification=True,
        related_date="FIRST_SUBMISSION_DEADLINE",
        roles=[EventRole.ATTENDEE],
    )

    students_fee_speaker = FareSchema(
        name="Speakers students Only Fee",
        description="Only Students with certificate",
        value="60",
        currency="ARS",
        need_verification=True,
        related_date="SECOND_SUBMISSION_DEADLINE",
        roles=[EventRole.SPEAKER],
    )
    pricing_config = PricingSchema(pricing=[students_fee_attendee, students_fee_speaker])

    response = await client.put(
        f"/events/{create_event['id']}/configuration/pricing",
        json=jsonable_encoder(pricing_config),
        headers=create_headers(admin_data.id),
    )
    assert response.status_code == 204

    response = await client.get(f"/events/{create_event['id']}/public", headers=create_headers(admin_data.id))

    assert response.status_code == 200
    pricing = response.json()["pricing"]
    assert len(pricing) == 2

    assert pricing[0]["name"] == students_fee_attendee.name
    assert pricing[0]["description"] == students_fee_attendee.description
    assert pricing[0]["value"] == students_fee_attendee.value
    assert pricing[0]["currency"] == students_fee_attendee.currency
    assert pricing[0]["need_verification"] == students_fee_attendee.need_verification
    assert pricing[0]["related_date"] == students_fee_attendee.related_date
    assert pricing[0]["roles"] == students_fee_attendee.roles

    assert pricing[1]["name"] == students_fee_speaker.name
    assert pricing[1]["description"] == students_fee_speaker.description
    assert pricing[1]["value"] == students_fee_speaker.value
    assert pricing[1]["currency"] == students_fee_speaker.currency
    assert pricing[1]["need_verification"] == students_fee_speaker.need_verification
    assert pricing[1]["related_date"] == students_fee_speaker.related_date
    assert pricing[1]["roles"] == students_fee_speaker.roles
