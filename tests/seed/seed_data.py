#!/usr/bin/env python3
"""
Seed test data for Freelance Platform v1.1
Creates 3 users per role + ~40 test records across all tables
"""
import sys
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.user import User, Profile, UserRole
from app.models.category import Category
from app.models.project import Project, ProjectStatus, Proposal, ProposalStatus
from app.models.notification import Notification
from app.models.feedback import Feedback
from app.models.review import Review
from app.models.audit import AuditLog
from app.models.system_warning import SystemWarning
from app.models.message import Message
from passlib.context import CryptContext

# Use pwd_context directly
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """Hash password safely"""
    return pwd_context.hash(password)

def seed_data():
    """Seed database with test data"""
    db = SessionLocal()
    
    try:
        print("🌱 Starting data seeding...\n")
        
        # ========== USERS & PROFILES ==========
        print("📝 Creating Users (3 per role)...")
        
        users = []
        
        # ADMIN users
        for i in range(1, 4):
            user = User(
                email=f"admin{i}@freelance.example.com",
                hashed_password=hash_password(f"admin{i}pass"),
                full_name=f"Admin User {i}",
                role=UserRole.ADMIN,
                is_active=True,
                is_suspended=False,
                failed_login_attempts=0
            )
            db.add(user)
            users.append(("ADMIN", user, i))
        
        # CLIENT users
        for i in range(1, 4):
            user = User(
                email=f"client{i}@freelance.example.com",
                hashed_password=hash_password(f"client{i}pass"),
                full_name=f"Client User {i}",
                role=UserRole.CLIENT,
                is_active=True,
                is_suspended=False,
                failed_login_attempts=0
            )
            db.add(user)
            users.append(("CLIENT", user, i))
        
        # FREELANCE users
        for i in range(1, 4):
            user = User(
                email=f"freelancer{i}@freelance.example.com",
                hashed_password=hash_password(f"freelancer{i}pass"),
                full_name=f"Freelancer User {i}",
                role=UserRole.FREELANCE,
                is_active=True,
                is_suspended=False,
                failed_login_attempts=0
            )
            db.add(user)
            users.append(("FREELANCE", user, i))
        
        db.commit()
        print(f"✓ Created {len(users)} users (9 total)")
        
        # Create profiles for all users
        for role, user, idx in users:
            profile = Profile(
                user_id=user.id,
                bio=f"Bio for {role} #{idx}",
                skills="Python, FastAPI, PostgreSQL" if role == "FREELANCE" else None,
                rating_average=4.5 if role == "FREELANCE" else 0.0,
                avatar_url=f"https://avatar.local/{role.lower()}{idx}.jpg",
                identity_verified=(role == "FREELANCE")  # Freelancers have verified identity
            )
            db.add(profile)
        
        db.commit()
        print("✓ Created profiles for all users")
        
        # ========== CATEGORIES ==========
        print("\n🏷️  Creating Categories...")
        
        categories_data = [
            ("Plomberie", True),
            ("Électricité", True),
            ("Menuiserie", True),
            ("Peinture", True),
            ("Nettoyage", True),
            ("Jardinerie", True),
            ("Réparations", True),
            ("Déménagement", True),
        ]
        
        categories = []
        for name, is_active in categories_data:
            cat = Category(name=name, is_active=is_active)
            db.add(cat)
            categories.append(cat)
        
        db.commit()
        print(f"✓ Created {len(categories)} categories")
        
        # Get user references for easier access
        admins = [u for r, u, i in users if r == "ADMIN"]
        clients = [u for r, u, i in users if r == "CLIENT"]
        freelancers = [u for r, u, i in users if r == "FREELANCE"]
        
        # ========== PROJECTS (TASKS) ==========
        print("\n📋 Creating Projects (Tasks)...")
        
        statuses = [
            ProjectStatus.OPEN,
            ProjectStatus.IN_PROGRESS,
            ProjectStatus.ARRIVED,
            ProjectStatus.FINISHED,
            ProjectStatus.COMPLETED,
        ]
        
        projects = []
        now = datetime.utcnow()
        
        for idx, client in enumerate(clients):
            for status_idx, status in enumerate(statuses):
                project = Project(
                    client_id=client.id,
                    category_id=categories[idx % len(categories)].id,
                    title=f"Tâche {status.value} - {client.full_name} #{status_idx + 1}",
                    description=f"Description de la tâche - Status: {status.value}. Lorem ipsum dolor sit amet.",
                    localisation=f"123 Rue de {categories[idx % len(categories)].name}, Paris, France",
                    scheduled_at=now + timedelta(days=idx + status_idx + 1),
                    status=status,
                    created_at=now - timedelta(days=10 - status_idx)
                )
                db.add(project)
                projects.append(project)
        
        db.commit()
        print(f"✓ Created {len(projects)} projects")
        
        # ========== PROPOSALS ==========
        print("\n💼 Creating Proposals...")
        
        proposals = []
        for project in projects:
            if project.status in [ProjectStatus.OPEN, ProjectStatus.IN_PROGRESS]:
                # Each OPEN/IN_PROGRESS project has 1-3 proposals
                for freq in range(1, min(4, len(freelancers) + 1)):
                    freelancer = freelancers[freq - 1]
                    
                    # First proposal is usually accepted for IN_PROGRESS projects
                    status = ProposalStatus.ACCEPTED if (freq == 1 and project.status == ProjectStatus.IN_PROGRESS) else ProposalStatus.PENDING
                    
                    proposal = Proposal(
                        project_id=project.id,
                        freelance_id=freelancer.id,
                        message=f"Candidature de {freelancer.full_name} - Je peux faire ce travail rapidement et efficacement!",
                        proposed_price=100.0 + (freq * 20),
                        status=status,
                        created_at=datetime.utcnow() - timedelta(days=5 - freq)
                    )
                    db.add(proposal)
                    proposals.append(proposal)
        
        db.commit()
        print(f"✓ Created {len(proposals)} proposals")
        
        # ========== REVIEWS ==========
        print("\n⭐ Creating Reviews...")
        
        reviews = []
        for completed_project in [p for p in projects if p.status == ProjectStatus.COMPLETED]:
            # Client reviews freelancer
            proposal = db.query(Proposal).filter(
                Proposal.project_id == completed_project.id,
                Proposal.status == ProposalStatus.ACCEPTED
            ).first()
            
            if proposal:
                review = Review(
                    project_id=completed_project.id,
                    reviewer_id=completed_project.client_id,
                    reviewee_id=proposal.freelance_id,
                    rating=4 + (hash(completed_project.id) % 2),
                    comment="Excellent travail, très satisfait!",
                    created_at=datetime.utcnow() - timedelta(days=1)
                )
                db.add(review)
                reviews.append(review)
        
        db.commit()
        print(f"✓ Created {len(reviews)} reviews")
        
        # ========== NOTIFICATIONS ==========
        print("\n🔔 Creating Notifications...")
        
        notifications = []
        for user in users[:5]:  # Only for first 5 users
            role, user_obj, idx = user
            notif_count = 3
            
            for i in range(notif_count):
                notif = Notification(
                    user_id=user_obj.id,
                    title=f"Notification #{i + 1}",
                    content=f"This is notification #{i + 1} for {user_obj.full_name}",
                    type="INFO" if i % 2 == 0 else "ALERT",
                    is_read=(i % 3 == 0),  # Some are read
                    created_at=datetime.utcnow() - timedelta(hours=i + 1)
                )
                db.add(notif)
                notifications.append(notif)
        
        db.commit()
        print(f"✓ Created {len(notifications)} notifications")
        
        # ========== FEEDBACKS ==========
        print("\n💬 Creating Feedbacks...")
        
        feedbacks = []
        for idx, client in enumerate(clients):
            feedback = Feedback(
                user_id=client.id,
                subject=f"Feedback subject #{idx + 1}",
                content=f"This is feedback content from {client.full_name}. Issue: something not working properly.",
                admin_reply=f"Thank you for your feedback. We will investigate this issue." if idx == 0 else None,
                status="REPLIED" if idx == 0 else "PENDING",
                created_at=datetime.utcnow() - timedelta(days=idx + 1)
            )
            db.add(feedback)
            feedbacks.append(feedback)
            
            # Add freelancer feedback too
            if idx < len(freelancers):
                feedback2 = Feedback(
                    user_id=freelancers[idx].id,
                    subject=f"Freelancer feedback #{idx + 1}",
                    content=f"Feedback from {freelancers[idx].full_name} about platform improvements.",
                    admin_reply=None,
                    status="PENDING",
                    created_at=datetime.utcnow() - timedelta(days=idx + 2)
                )
                db.add(feedback2)
                feedbacks.append(feedback2)
        
        db.commit()
        print(f"✓ Created {len(feedbacks)} feedbacks")
        
        # ========== AUDIT LOGS ==========
        print("\n📊 Creating Audit Logs...")
        
        audit_logs = []
        actions = [
            ("SUSPEND", "USER", admins[0].id),
            ("ACTIVATE", "USER", admins[0].id),
            ("VERIFY_IDENTITY", "PROFILE", freelancers[0].id),
            ("DELETE_PROJECT", "PROJECT", projects[0].id if projects else None),
            ("REPLY_FEEDBACK", "FEEDBACK", feedbacks[0].id if feedbacks else None),
            ("CREATE_CATEGORY", "CATEGORY", categories[0].id if categories else None),
            ("BROADCAST", "NOTIFICATION", None),
        ]
        
        for idx, (action, target_type, target_id) in enumerate(actions):
            if target_id is not None or action == "BROADCAST":
                log = AuditLog(
                    user_id=None,  # System action
                    action=action,
                    target_type=target_type,
                    target_id=target_id,
                    details=f"Action: {action} on {target_type}",
                    created_at=datetime.utcnow() - timedelta(hours=idx)
                )
                db.add(log)
                audit_logs.append(log)
        
        db.commit()
        print(f"✓ Created {len(audit_logs)} audit logs")
        
        # ========== SYSTEM WARNINGS ==========
        print("\n⚠️  Creating System Warnings...")
        
        warnings = []
        for idx, freelancer in enumerate(freelancers):
            if idx == 0:
                # One unresolved brute force warning
                warning = SystemWarning(
                    warning_type="BRUTE_FORCE",
                    user_id=freelancer.id,
                    description=f"Account {freelancer.email} suspended after 10 failed login attempts.",
                    is_resolved=False,
                    created_at=datetime.utcnow() - timedelta(hours=2)
                )
            else:
                # Resolved warning
                warning = SystemWarning(
                    warning_type="ANOMALY",
                    user_id=freelancer.id,
                    description=f"Unusual activity detected for {freelancer.email}",
                    is_resolved=True,
                    created_at=datetime.utcnow() - timedelta(days=1)
                )
            db.add(warning)
            warnings.append(warning)
        
        db.commit()
        print(f"✓ Created {len(warnings)} system warnings")
        
        # ========== MESSAGES ==========
        print("\n💌 Creating Messages...")
        
        messages = []
        for project in projects[:3]:  # Only for first 3 projects
            proposal = db.query(Proposal).filter(
                Proposal.project_id == project.id,
                Proposal.status == ProposalStatus.ACCEPTED
            ).first()
            
            if proposal:
                for i in range(2):
                    message = Message(
                        project_id=project.id,
                        sender_id=project.client_id if i == 0 else proposal.freelance_id,
                        receiver_id=proposal.freelance_id if i == 0 else project.client_id,
                        content=f"Message #{i + 1}: {'Client asking about progress' if i == 0 else 'Freelancer providing update'}",
                        is_read=(i % 2 == 0),
                        created_at=datetime.utcnow() - timedelta(hours=i + 1)
                    )
                    db.add(message)
                    messages.append(message)
        
        db.commit()
        print(f"✓ Created {len(messages)} messages")
        
        # ========== SUMMARY ==========
        print("\n" + "="*50)
        print("✅ DATA SEEDING COMPLETE!")
        print("="*50)
        
        summary = {
            "Users": len(users),
            "Profiles": len(users),
            "Categories": len(categories),
            "Projects": len(projects),
            "Proposals": len(proposals),
            "Reviews": len(reviews),
            "Notifications": len(notifications),
            "Feedbacks": len(feedbacks),
            "Audit Logs": len(audit_logs),
            "System Warnings": len(warnings),
            "Messages": len(messages),
        }
        
        print("\n📊 Data Summary:")
        total = 0
        for table, count in summary.items():
            print(f"  • {table:.<20} {count:>3}")
            total += count
        print(f"  {'TOTAL':.<20} {total:>3}")
        
        print("\n🔑 Default Credentials:")
        print("  Admin:      admin1@freelance.example.com / admin1pass")
        print("  Client:     client1@freelance.example.com / client1pass")
        print("  Freelancer: freelancer1@freelance.example.com / freelancer1pass")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"\n❌ Error during seeding: {e}")
        import traceback
        traceback.print_exc()
        db.close()
        return False

if __name__ == "__main__":
    success = seed_data()
    sys.exit(0 if success else 1)
