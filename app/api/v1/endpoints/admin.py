from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.api.v1.deps import get_db, get_current_admin
from app.services.admin_service import (
    toggle_user_suspension,
    verify_user_identity,
    delete_project_admin,
    get_platform_stats,
    get_admin_overview,
    get_admin_users,
    get_admin_projects,
    get_admin_reports,
    resolve_report_admin,
    get_audit_logs,
    get_system_warnings,
    resolve_system_warning,
    get_pending_feedbacks,
    reply_to_feedback,
    create_category,
    get_categories,
    update_category,
    broadcast_notification,
)
from app.schemas.user import UserOut
from app.schemas.project import ProjectOut
from app.schemas.feedback import FeedbackOut, FeedbackReply
from app.schemas.audit import AuditLogOut
from app.schemas.system_warning import SystemWarningOut
from app.schemas.category import CategoryOut, CategoryCreate
from app.schemas.broadcast import BroadcastNotification
from app.models.user import Profile

router = APIRouter()

# ========================
# OPERATIONS OVERVIEW
# ========================

@router.get("/overview")
def admin_overview(db: Session = Depends(get_db), current_admin = Depends(get_current_admin)):
    """Global admin dashboard with KPI, recent tasks and active users."""
    return get_admin_overview(db)

# ========================
# USER MANAGEMENT
# ========================

@router.get("/users", response_model=List[UserOut])
def list_users(
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    q: Optional[str] = Query(None),
    role: Optional[str] = Query(None),
    active: Optional[bool] = Query(None),
    suspended: Optional[bool] = Query(None),
):
    """List users with filters for admin operational view."""
    return get_admin_users(db, skip=skip, limit=limit, q=q, role=role, active=active, suspended=suspended)

@router.post("/users/{user_id}/suspend", response_model=UserOut)
def suspend_user(user_id: int, db: Session = Depends(get_db), current_admin = Depends(get_current_admin)):
    """Suspend a user account"""
    return toggle_user_suspension(db, user_id, True)

@router.post("/users/{user_id}/activate", response_model=UserOut)
def activate_user(user_id: int, db: Session = Depends(get_db), current_admin = Depends(get_current_admin)):
    """Activate a user account"""
    return toggle_user_suspension(db, user_id, False)

@router.put("/users/{user_id}/verify-identity")
def verify_identity(user_id: int, db: Session = Depends(get_db), current_admin = Depends(get_current_admin)):
    """Verify freelancer identity"""
    profile = verify_user_identity(db, user_id)
    return {"message": "Identity verified", "profile_id": profile.id}

# ========================
# PROJECT MANAGEMENT
# ========================

@router.get("/projects", response_model=List[ProjectOut])
def list_projects(
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    status: Optional[str] = Query(None),
    category_id: Optional[int] = Query(None),
):
    """List tasks/projects with filters for admin moderation and operations."""
    return get_admin_projects(db, skip=skip, limit=limit, status=status, category_id=category_id)

@router.delete("/projects/{project_id}")
def delete_project(project_id: int, db: Session = Depends(get_db), current_admin = Depends(get_current_admin)):
    """Delete a project (admin only)"""
    return delete_project_admin(db, project_id)

# ========================
# REPORTS / DISPUTES
# ========================

@router.get("/reports")
def list_reports(
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    status: Optional[str] = Query(None),
):
    """List user reports and dispute tickets."""
    return get_admin_reports(db, skip=skip, limit=limit, status=status)

@router.post("/reports/{report_id}/resolve")
def resolve_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin),
    status: str = Query("RESOLVED"),
):
    """Resolve a report or dispute claim."""
    return resolve_report_admin(db, report_id, status=status)

# ========================
# STATISTICS & MONITORING
# ========================

@router.get("/stats")
def platform_stats(db: Session = Depends(get_db), current_admin = Depends(get_current_admin)):
    """Get platform statistics"""
    return get_platform_stats(db)

# ========================
# AUDIT LOGS
# ========================

@router.get("/audit-logs", response_model=List[AuditLogOut])
def list_audit_logs(
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    action: str = Query(None),
    user_id: int = Query(None),
):
    """Get audit logs with optional filtering"""
    return get_audit_logs(db, skip=skip, limit=limit, action=action, user_id=user_id)

# ========================
# SYSTEM WARNINGS
# ========================

@router.get("/system-warnings", response_model=List[SystemWarningOut])
def list_system_warnings(
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    resolved: bool = Query(None),
):
    """Get system warnings with optional filtering"""
    return get_system_warnings(db, skip=skip, limit=limit, resolved=resolved)

@router.put("/system-warnings/{warning_id}/resolve", response_model=SystemWarningOut)
def resolve_warning(
    warning_id: int,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin),
):
    """Mark system warning as resolved"""
    return resolve_system_warning(db, warning_id)

# ========================
# FEEDBACK MANAGEMENT
# ========================

@router.get("/feedbacks/pending", response_model=List[FeedbackOut])
def list_pending_feedbacks(
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
):
    """Get pending feedbacks"""
    return get_pending_feedbacks(db, skip=skip, limit=limit)

@router.post("/feedbacks/{feedback_id}/reply", response_model=FeedbackOut)
def reply_feedback(
    feedback_id: int,
    reply_data: FeedbackReply,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin),
):
    """Reply to user feedback"""
    return reply_to_feedback(db, feedback_id, reply_data)

# ========================
# CATEGORY MANAGEMENT
# ========================

@router.post("/categories", response_model=CategoryOut)
def create_new_category(
    category_in: CategoryCreate,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin),
):
    """Create a new category"""
    return create_category(db, category_in.name)

@router.get("/categories", response_model=List[CategoryOut])
def list_categories(
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin),
    active_only: bool = Query(True),
):
    """List all categories"""
    return get_categories(db, active_only=active_only)

@router.put("/categories/{category_id}", response_model=CategoryOut)
def update_cat(
    category_id: int,
    category_in: CategoryCreate,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin),
):
    """Update category"""
    return update_category(db, category_id, name=category_in.name, is_active=category_in.is_active)

# ========================
# BROADCAST NOTIFICATIONS
# ========================

@router.post("/broadcast")
def send_broadcast(
    broadcast_data: BroadcastNotification,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin),
):
    """Send notification to all users or specific role"""
    return broadcast_notification(
        db,
        title=broadcast_data.title,
        content=broadcast_data.content,
        target_role=broadcast_data.target_role,
    )

# ========================
# LOCATION MANAGEMENT (Pays / Villes / Quartiers)
# ========================

from fastapi import HTTPException
from app.models.location import Country, City, District
from app.schemas.location import (
    CountryCreate, CountryUpdate, CountryOut,
    CityCreate, CityUpdate, CityOut,
    DistrictCreate, DistrictUpdate, DistrictOut,
)

# --- Countries ---
@router.post("/locations/countries", response_model=CountryOut)
def create_country(data: CountryCreate, db: Session = Depends(get_db), current_admin = Depends(get_current_admin)):
    """Create a new country"""
    existing = db.query(Country).filter(Country.code == data.code.upper()).first()
    if existing:
        raise HTTPException(status_code=400, detail="Ce pays existe déjà")
    country = Country(name=data.name, code=data.code.upper())
    db.add(country)
    db.commit()
    db.refresh(country)
    return country

@router.put("/locations/countries/{country_id}", response_model=CountryOut)
def update_country(country_id: int, data: CountryUpdate, db: Session = Depends(get_db), current_admin = Depends(get_current_admin)):
    """Update a country"""
    country = db.query(Country).filter(Country.id == country_id).first()
    if not country:
        raise HTTPException(status_code=404, detail="Pays introuvable")
    if data.name is not None: country.name = data.name
    if data.code is not None: country.code = data.code.upper()
    if data.is_active is not None: country.is_active = data.is_active
    db.commit()
    db.refresh(country)
    return country

# --- Cities ---
@router.post("/locations/cities", response_model=CityOut)
def create_city(data: CityCreate, db: Session = Depends(get_db), current_admin = Depends(get_current_admin)):
    """Create a new city"""
    country = db.query(Country).filter(Country.id == data.country_id).first()
    if not country:
        raise HTTPException(status_code=404, detail="Pays introuvable")
    city = City(name=data.name, latitude=data.latitude, longitude=data.longitude, country_id=data.country_id)
    db.add(city)
    db.commit()
    db.refresh(city)
    return city

@router.put("/locations/cities/{city_id}", response_model=CityOut)
def update_city(city_id: int, data: CityUpdate, db: Session = Depends(get_db), current_admin = Depends(get_current_admin)):
    """Update a city"""
    city = db.query(City).filter(City.id == city_id).first()
    if not city:
        raise HTTPException(status_code=404, detail="Ville introuvable")
    if data.name is not None: city.name = data.name
    if data.latitude is not None: city.latitude = data.latitude
    if data.longitude is not None: city.longitude = data.longitude
    if data.is_active is not None: city.is_active = data.is_active
    db.commit()
    db.refresh(city)
    return city

@router.delete("/locations/cities/{city_id}")
def delete_city(city_id: int, db: Session = Depends(get_db), current_admin = Depends(get_current_admin)):
    """Delete a city and its districts"""
    city = db.query(City).filter(City.id == city_id).first()
    if not city:
        raise HTTPException(status_code=404, detail="Ville introuvable")
    db.delete(city)
    db.commit()
    return {"message": f"Ville '{city.name}' supprimée"}

# --- Districts (Quartiers) ---
@router.post("/locations/districts", response_model=DistrictOut)
def create_district(data: DistrictCreate, db: Session = Depends(get_db), current_admin = Depends(get_current_admin)):
    """Create a new district/quartier"""
    city = db.query(City).filter(City.id == data.city_id).first()
    if not city:
        raise HTTPException(status_code=404, detail="Ville introuvable")
    district = District(name=data.name, city_id=data.city_id, latitude=data.latitude, longitude=data.longitude)
    db.add(district)
    db.commit()
    db.refresh(district)
    return district

@router.put("/locations/districts/{district_id}", response_model=DistrictOut)
def update_district(district_id: int, data: DistrictUpdate, db: Session = Depends(get_db), current_admin = Depends(get_current_admin)):
    """Update a district"""
    district = db.query(District).filter(District.id == district_id).first()
    if not district:
        raise HTTPException(status_code=404, detail="Quartier introuvable")
    if data.name is not None: district.name = data.name
    if data.latitude is not None: district.latitude = data.latitude
    if data.longitude is not None: district.longitude = data.longitude
    if data.is_active is not None: district.is_active = data.is_active
    db.commit()
    db.refresh(district)
    return district

@router.delete("/locations/districts/{district_id}")
def delete_district(district_id: int, db: Session = Depends(get_db), current_admin = Depends(get_current_admin)):
    """Delete a district"""
    district = db.query(District).filter(District.id == district_id).first()
    if not district:
        raise HTTPException(status_code=404, detail="Quartier introuvable")
    db.delete(district)
    db.commit()
    return {"message": f"Quartier '{district.name}' supprimé"}

