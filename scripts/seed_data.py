import os
import sys
from datetime import datetime

# Add the project root to the python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import SessionLocal
from app.models.user import User
from app.models.task import Task, TaskStatus
from app.models.application import Application, ApplicationStatus
from app.models.message import Message
from app.models.notification import Notification
from app.models.review import Review, ReviewType
from app.core.security import get_password_hash

def seed_db():
    db = SessionLocal()

    print("Cleaning existing data...")
    db.query(Review).delete()
    db.query(Notification).delete()
    db.query(Message).delete()
    db.query(Application).delete()
    db.query(Task).delete()
    db.query(User).delete()
    db.commit()

    print("Seeding Users...")
    admin = User(
        full_name="Admin User",
        email="admin@example.com",
        hashed_password=get_password_hash("admin123"),
        is_admin=True,
        is_active=True
    )
    
    client1 = User(
        full_name="Alice Client",
        email="alice@example.com",
        hashed_password=get_password_hash("client123"),
        is_client=True,
        is_active=True,
        location="Paris"
    )
    
    client2 = User(
        full_name="Bob Client",
        email="bob@example.com",
        hashed_password=get_password_hash("client123"),
        is_client=True,
        is_active=True,
        location="Lyon"
    )

    freelancer1 = User(
        full_name="Charlie Dev",
        email="charlie@example.com",
        hashed_password=get_password_hash("free123"),
        is_freelancer=True,
        is_active=True,
        location="Marseille"
    )

    freelancer2 = User(
        full_name="Diana Designer",
        email="diana@example.com",
        hashed_password=get_password_hash("free123"),
        is_freelancer=True,
        is_active=True,
        location="Toulouse"
    )

    freelancer3 = User(
        full_name="Eve Writer",
        email="eve@example.com",
        hashed_password=get_password_hash("free123"),
        is_freelancer=True,
        is_active=True,
        location="Nice"
    )

    db.add_all([admin, client1, client2, freelancer1, freelancer2, freelancer3])
    db.commit()

    print("Seeding Tasks...")
    task1 = Task(title="Build a React app", description="Need a responsive single page app", price=1500.0, location="Remote", status=TaskStatus.VALIDATED, client_id=client1.id)
    task2 = Task(title="Design Logo", description="A modern minimalist logo", price=300.0, location="Remote", status=TaskStatus.PENDING, client_id=client2.id)
    task3 = Task(title="Write Blog Posts", description="5 tech articles", price=250.0, location="Paris", status=TaskStatus.EXECUTED, client_id=client1.id)

    db.add_all([task1, task2, task3])
    db.commit()

    print("Seeding Applications...")
    app1 = Application(message="I have 5 years of React experience.", status=ApplicationStatus.ACCEPTED, task_id=task1.id, freelance_id=freelancer1.id)
    app2 = Application(message="I can design this for you.", status=ApplicationStatus.PENDING, task_id=task2.id, freelance_id=freelancer2.id)
    app3 = Application(message="I write excellent tech articles.", status=ApplicationStatus.ACCEPTED, task_id=task3.id, freelance_id=freelancer3.id)
    app4 = Application(message="Also applying for React.", status=ApplicationStatus.REJECTED, task_id=task1.id, freelance_id=freelancer3.id)

    db.add_all([app1, app2, app3, app4])
    db.commit()

    print("Seeding Messages...")
    msg1 = Message(content="Hi Charlie, your application is accepted. Can we start tomorrow?", sender_id=client1.id, receiver_id=freelancer1.id, task_id=task1.id)
    msg2 = Message(content="Yes! I am ready.", sender_id=freelancer1.id, receiver_id=client1.id, task_id=task1.id)
    msg3 = Message(content="Please send me the repo access.", sender_id=freelancer1.id, receiver_id=client1.id, task_id=task1.id)

    db.add_all([msg1, msg2, msg3])
    db.commit()

    print("Seeding Notifications...")
    notif1 = Notification(message="Your application for 'Build a React app' was accepted.", is_read=False, user_id=freelancer1.id)
    notif2 = Notification(message="You have a new message from Alice Client.", is_read=True, user_id=freelancer1.id)

    db.add_all([notif1, notif2])
    db.commit()

    print("Seeding Reviews...")
    rev1 = Review(content="The site layout could be improved on mobile.", review_type=ReviewType.IMPROVEMENT, user_id=freelancer2.id)
    rev2 = Review(content="I love how easy it is to find tasks!", review_type=ReviewType.SUGGESTION, user_id=freelancer1.id)

    db.add_all([rev1, rev2])
    db.commit()

    print("Database seeding completed successfully.")
    db.close()

if __name__ == "__main__":
    seed_db()
