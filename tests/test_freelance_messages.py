from app.models.message import Message
from tests.conftest import auth_headers, create_user


def test_freelance_can_read_existing_conversation_without_accepted_application(client, db_session):
    client_user = create_user(client, "client@example.com", "password123", is_client=True)
    freelancer_user = create_user(client, "freelancer@example.com", "password123", is_freelancer=True)

    db_session.add(
        Message(
            content="Bonjour",
            sender_id=client_user["id"],
            receiver_id=freelancer_user["id"],
        )
    )
    db_session.commit()

    headers = auth_headers(client, "freelancer@example.com", "password123")
    response = client.get(
        f"/api/v1/freelance/messages/{client_user['id']}",
        headers=headers,
    )

    assert response.status_code == 200, response.text
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["content"] == "Bonjour"
