from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class RegisterInput(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(min_length=6, max_length=100)


class LoginInput(BaseModel):
    email: EmailStr
    password: str


class UserOutput(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str
    role: str


class LoginOutput(BaseModel):
    token: str
    user: UserOutput


class ServiceInput(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    duration_minutes: int = Field(gt=0, le=480)
    price_cents: int = Field(ge=0)
    description: str = Field(default='', max_length=1000)


class ServiceOutput(ServiceInput):
    model_config = ConfigDict(from_attributes=True)

    id: int


class TherapistOutput(BaseModel):
    id: int
    name: str
    email: str
    bio: str
    service_ids: list[int]


class AvailabilityInput(BaseModel):
    start_time: datetime
    end_time: datetime


class AvailabilityOutput(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    therapist_id: int
    start_time: datetime
    end_time: datetime
    is_available: bool


class BookingInput(BaseModel):
    therapist_id: int
    service_id: int
    start_time: datetime
    note: str = Field(default='', max_length=1000)


class BookingStatusInput(BaseModel):
    status: str


class BookingOutput(BaseModel):
    id: int
    client_id: int
    client_name: str
    therapist_id: int
    therapist_name: str
    service_id: int
    service_name: str
    start_time: datetime
    end_time: datetime
    status: str
    note: str
