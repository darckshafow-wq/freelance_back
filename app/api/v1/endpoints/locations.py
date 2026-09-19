from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.api.v1.deps import get_db, get_current_user
from app.models.location import Country, City, District
from app.schemas.location import (
    CountryOut, CountryWithCitiesOut,
    CityOut, CityWithDistrictsOut,
    DistrictOut,
)

router = APIRouter()


@router.get("/countries", response_model=List[CountryOut])
def list_countries(db: Session = Depends(get_db)):
    """List all active countries (public endpoint)."""
    return db.query(Country).filter(Country.is_active.is_(True)).order_by(Country.name).all()


@router.get("/countries/{country_id}/cities", response_model=List[CityOut])
def list_cities(country_id: int, db: Session = Depends(get_db)):
    """List all active cities for a country."""
    return (
        db.query(City)
        .filter(City.country_id == country_id, City.is_active.is_(True))
        .order_by(City.name)
        .all()
    )


@router.get("/cities/{city_id}/districts", response_model=List[DistrictOut])
def list_districts(city_id: int, db: Session = Depends(get_db)):
    """List all active districts for a city."""
    return (
        db.query(District)
        .filter(District.city_id == city_id, District.is_active.is_(True))
        .order_by(District.name)
        .all()
    )


@router.get("/countries/{country_id}/full", response_model=CountryWithCitiesOut)
def get_country_full(country_id: int, db: Session = Depends(get_db)):
    """Get a country with all its cities and districts (for frontend cache)."""
    country = db.query(Country).filter(Country.id == country_id).first()
    if not country:
        raise HTTPException(status_code=404, detail="Pays introuvable")
    return country

