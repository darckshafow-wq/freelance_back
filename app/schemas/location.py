from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


# ---- Country ----
class CountryBase(BaseModel):
    name: str
    code: str

class CountryCreate(CountryBase):
    pass

class CountryUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    is_active: Optional[bool] = None

class CountryOut(CountryBase):
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ---- City ----
class CityBase(BaseModel):
    name: str
    latitude: float
    longitude: float
    country_id: int

class CityCreate(CityBase):
    pass

class CityUpdate(BaseModel):
    name: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    is_active: Optional[bool] = None

class CityOut(CityBase):
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ---- District (Quartier) ----
class DistrictBase(BaseModel):
    name: str
    city_id: int
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class DistrictCreate(DistrictBase):
    pass

class DistrictUpdate(BaseModel):
    name: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    is_active: Optional[bool] = None

class DistrictOut(DistrictBase):
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ---- Nested output for frontend dropdown ----
class CityWithDistrictsOut(CityOut):
    districts: List[DistrictOut] = []

class CountryWithCitiesOut(CountryOut):
    cities: List[CityWithDistrictsOut] = []

