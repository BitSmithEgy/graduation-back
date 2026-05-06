import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import uuid
import datetime

from main import app
from database import Base, get_db
from models import RoleEnum

# Set up an in-memory SQLite database for testing to avoid polluting real DB
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables in the in-memory database
Base.metadata.create_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

# Override the get_db dependency to use the test database
app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

@pytest.fixture(scope="module")
def admin_token():
    db = TestingSessionLocal()
    from models import User
    from utils import hash_password, create_access_token
    
    admin_user = User(
        email="admin@test.com",
        phone="0000000000",
        full_name="Admin User",
        password_hash=hash_password("adminpass"),
        role=RoleEnum.admin
    )
    db.add(admin_user)
    db.commit()
    db.refresh(admin_user)
    
    token = create_access_token(data={"user_id": admin_user.uuid, "role": "admin"})
    db.close()
    return token

@pytest.fixture(scope="module")
def clinic_data():
    return {
        "email": f"clinic_{uuid.uuid4().hex[:6]}@test.com",
        "phone": f"111{uuid.uuid4().hex[:6]}",
        "full_name": "Clinic User",
        "password": "clinicpass",
        "clinic": {
            "name": "Test Clinic",
            "address": "123 Test St",
            "phone": "01000000000",
            "email": "contact@testclinic.com"
        }
    }

@pytest.fixture(scope="module")
def user_data():
    return {
        "email": f"user_{uuid.uuid4().hex[:6]}@test.com",
        "phone": f"222{uuid.uuid4().hex[:6]}",
        "full_name": "Normal User",
        "password": "userpass",
    }

def test_root():
    response = client.get("/")
    assert response.status_code == 200

def test_register_clinic(clinic_data):
    response = client.post("/users/register/clinic", json=clinic_data)
    assert response.status_code == 201
    data = response.json()
    assert "uuid" in data
    assert data["role"] == "clinic"

def test_login_clinic(clinic_data):
    response = client.post("/users/login", json={
        "email": clinic_data["email"],
        "password": clinic_data["password"]
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    return data["access_token"]

def test_register_user(user_data):
    response = client.post("/users/register/user", json=user_data)
    assert response.status_code == 201
    data = response.json()
    assert "uuid" in data
    assert data["role"] == "user"

def test_login_user(user_data):
    response = client.post("/users/login", json={
        "email": user_data["email"],
        "password": user_data["password"]
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    return data["access_token"]

def test_specializations_and_doctors(admin_token, clinic_data):
    # 1. Create specialization (admin)
    headers_admin = {"Authorization": f"Bearer {admin_token}"}
    spec_payload = {
        "name_en": "Cardiology",
        "name_ar": "قلبية"
    }
    resp = client.post("/specializations/", json=spec_payload, headers=headers_admin)
    assert resp.status_code == 201
    spec_id = resp.json()["id"]

    # 2. Login clinic
    clinic_token = test_login_clinic(clinic_data)
    headers_clinic = {"Authorization": f"Bearer {clinic_token}"}

    # 3. Create doctor
    doc_payload = {
        "specialization_id": spec_id,
        "full_name": "Dr. Smith"
    }
    resp = client.post("/doctors/", json=doc_payload, headers=headers_clinic)
    assert resp.status_code == 201
    doc_id = resp.json()["id"]

    # 4. Add availability
    avail_payload = {
        "day_of_week": 1, # Monday
        "start_time": "09:00:00",
        "end_time": "17:00:00",
        "slot_duration_minutes": 30
    }
    resp = client.post(f"/doctors/{doc_id}/availability/", json=avail_payload, headers=headers_clinic)
    assert resp.status_code == 201

def test_slots_and_bookings(clinic_data, user_data):
    clinic_token = test_login_clinic(clinic_data)
    headers_clinic = {"Authorization": f"Bearer {clinic_token}"}

    user_token = test_login_user(user_data)
    headers_user = {"Authorization": f"Bearer {user_token}"}
    
    docs_resp = client.get("/doctors/")
    docs = docs_resp.json()
    if not docs:
        return
    doc_id = docs[0]["id"]

    today = datetime.date.today()
    next_week = today + datetime.timedelta(days=7)
    
    # 1. Generate slots
    slot_gen_payload = {
        "doctor_id": doc_id,
        "from_date": today.isoformat(),
        "to_date": next_week.isoformat()
    }
    resp = client.post("/appointment-slots/generate", json=slot_gen_payload, headers=headers_clinic)
    # The status code might be 200 or 201 depending on the implementation
    assert resp.status_code in [200, 201]
    
    # 2. Fetch slots
    slots_resp = client.get(f"/appointment-slots/?doctor_id={doc_id}")
    slots = slots_resp.json()
    
    # Find an available slot
    available_slots = [s for s in slots if s["slot_status"] == "available"]
    if not available_slots:
        return
        
    slot_id = available_slots[0]["id"]
    
    # 3. User books the slot
    book_payload = {
        "slot_id": slot_id,
        "notes": "Testing booking",
        "booking_language": "en"
    }
    resp = client.post("/bookings/", json=book_payload, headers=headers_user)
    assert resp.status_code == 201
    booking_id = resp.json()["id"]
    
    # 4. Get user bookings
    resp = client.get("/bookings/me", headers=headers_user)
    assert resp.status_code == 200
    assert len(resp.json()) > 0
    
    # 5. Cancel booking
    resp = client.patch(f"/bookings/{booking_id}/cancel", headers=headers_user)
    assert resp.status_code == 200

if __name__ == "__main__":
    pytest.main(["-v", __file__])
