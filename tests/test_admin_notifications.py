from app.models.notifications import Notification as NotificationModel
from tests.conftest import auth_headers, create_user


def test_admin_broadcast_creates_notifications_for_matching_users(client, db_session):
    create_user(client, "admin@example.com", "password123", is_admin=True)
    create_user(client, "client@example.com", "password123", is_client=True)
    create_user(client, "freelancer@example.com", "password123", is_freelancer=True)

    headers = auth_headers(client, "admin@example.com", "password123")

    response = client.post(
        "/api/v1/admin/notifications/broadcast",
        headers=headers,
        params={"title": "Maintenance", "content": "Platform update", "target_role": "client"},
    )

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["created"] == 1
    assert payload["target_role"] == "client"

    history_response = client.get(
        "/api/v1/admin/notifications/broadcast",
        headers=headers,
    )
    assert history_response.status_code == 200, history_response.text
    history_payload = history_response.json()
    assert history_payload[0]["title"] == "Maintenance"
    assert history_payload[0]["body"] == "Platform update"

    notifications = db_session.query(NotificationModel).all()
    assert len(notifications) == 1
    assert notifications[0].message == "Maintenance: Platform update"
    assert notifications[0].user_id is not None
