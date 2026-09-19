#!/usr/bin/env python3
"""
Verification script - Display seeded test data
"""
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.user import User, UserRole
from app.models.category import Category
from app.models.project import Project, ProjectStatus, Proposal, ProposalStatus
from app.models.notification import Notification
from app.models.feedback import Feedback
from app.models.review import Review
from app.models.audit import AuditLog
from app.models.system_warning import SystemWarning
from app.models.message import Message

def verify_data():
    """Verify all seeded data"""
    db = SessionLocal()
    
    print("\n" + "="*60)
    print("📊 DATABASE VERIFICATION REPORT")
    print("="*60)
    
    # Users by role
    print("\n👥 USERS BY ROLE:")
    for role in [UserRole.ADMIN, UserRole.CLIENT, UserRole.FREELANCE]:
        count = db.query(User).filter(User.role == role).count()
        users = db.query(User).filter(User.role == role).all()
        print(f"  {role.value:.<15} {count:>2} users")
        for u in users:
            print(f"    • {u.email}")
    
    # Projects by status
    print("\n📋 PROJECTS BY STATUS:")
    total_projects = 0
    for status in [ProjectStatus.OPEN, ProjectStatus.IN_PROGRESS, ProjectStatus.ARRIVED, 
                   ProjectStatus.FINISHED, ProjectStatus.COMPLETED]:
        count = db.query(Project).filter(Project.status == status).count()
        total_projects += count
        print(f"  {status.value:.<15} {count:>2} projects")
    print(f"  {'TOTAL':.<15} {total_projects:>2} projects")
    
    # Proposals by status
    print("\n💼 PROPOSALS BY STATUS:")
    for status in [ProposalStatus.PENDING, ProposalStatus.ACCEPTED, ProposalStatus.REJECTED]:
        count = db.query(Proposal).filter(Proposal.status == status).count()
        print(f"  {status.value:.<15} {count:>2} proposals")
    
    # Other tables
    print("\n📊 OTHER TABLES:")
    tables = [
        ("Categories", Category),
        ("Notifications", Notification),
        ("Feedbacks", Feedback),
        ("Reviews", Review),
        ("Audit Logs", AuditLog),
        ("System Warnings", SystemWarning),
        ("Messages", Message),
    ]
    
    for name, model in tables:
        count = db.query(model).count()
        print(f"  {name:.<20} {count:>2} records")
    
    # Sample data
    print("\n📄 SAMPLE DATA:")
    
    print("\n  Sample Admin User:")
    admin = db.query(User).filter(User.role == UserRole.ADMIN).first()
    if admin:
        print(f"    Email: {admin.email}")
        print(f"    Name: {admin.full_name}")
        print(f"    Role: {admin.role.value}")
    
    print("\n  Sample Project:")
    project = db.query(Project).first()
    if project:
        print(f"    Title: {project.title}")
        print(f"    Status: {project.status.value}")
        print(f"    Location: {project.localisation}")
    
    print("\n  Sample Proposal:")
    proposal = db.query(Proposal).first()
    if proposal:
        print(f"    Price: ${proposal.proposed_price}")
        print(f"    Status: {proposal.status.value}")
        print(f"    Message: {proposal.message[:50]}...")
    
    print("\n  Sample Notification:")
    notif = db.query(Notification).first()
    if notif:
        print(f"    Title: {notif.title}")
        print(f"    Type: {notif.type}")
        print(f"    Read: {notif.is_read}")
    
    print("\n  Sample Feedback:")
    feedback = db.query(Feedback).first()
    if feedback:
        print(f"    Subject: {feedback.subject}")
        print(f"    Status: {feedback.status}")
        print(f"    Content: {feedback.content[:40]}...")
    
    # Quick stats
    print("\n" + "="*60)
    print("✅ VERIFICATION SUMMARY:")
    print("="*60)
    
    user_count = db.query(User).count()
    project_count = db.query(Project).count()
    proposal_count = db.query(Proposal).count()
    total_records = sum([
        user_count,
        db.query(Category).count(),
        project_count,
        proposal_count,
        db.query(Notification).count(),
        db.query(Feedback).count(),
        db.query(Review).count(),
        db.query(AuditLog).count(),
        db.query(SystemWarning).count(),
        db.query(Message).count(),
    ])
    
    print(f"  Total Users:     {user_count}")
    print(f"  Total Projects:  {project_count}")
    print(f"  Total Proposals: {proposal_count}")
    print(f"  Total Records:   {total_records}")
    
    print("\n🔑 TEST CREDENTIALS:")
    print("  ADMIN:      admin1@freelance.example.com / admin1pass")
    print("  CLIENT:     client1@freelance.example.com / client1pass")
    print("  FREELANCER: freelancer1@freelance.example.com / freelancer1pass")
    
    print("\n✨ Database is ready for API testing!")
    print("="*60 + "\n")
    
    db.close()

if __name__ == "__main__":
    verify_data()
