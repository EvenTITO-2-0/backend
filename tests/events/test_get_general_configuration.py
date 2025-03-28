from ..commontest import create_headers


async def test_get_event_configuration_organizer_gets_dates_pricing_review_skeleton_and_emails(
    client, create_user, create_event_creator, create_event_from_event_creator
):
    response = await client.get(
        f"/events/{create_event_from_event_creator}/configuration", headers=create_headers(create_event_creator["id"])
    )
    event_config = response.json()

    assert response.status_code == 200
    assert event_config["dates"] is not None
    assert len(event_config["pricing"]) == 0
    assert len(event_config["notification_mails"]) == 0
    assert len(event_config["review_skeleton"]["questions"]) == 0
    assert event_config["review_skeleton"]["recommendation"] is not None
    assert event_config["review_skeleton"]["recommendation"]["question"] == "Recomendación"
    assert event_config["review_skeleton"]["recommendation"]["type_question"] == "multiple_choice"
    assert event_config["review_skeleton"]["recommendation"]["more_than_one_answer_allowed"] is False
