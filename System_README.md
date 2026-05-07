# Graduation Project Backend API - System Documentation

This document outlines the system flows, user roles, and API workflows for the Graduation Project Backend.

## 1. System Overview
The system is a medical management platform that connects patients (Users), Doctors, and Clinics. It supports appointment booking, medical record management, AI-driven diagnostics (Diabetes & Radiology), and secure chat.

---

## 2. User Roles & Flows

### A. Patient (Regular User)
**Flow**: Register -> Login -> Manage Profile -> Search Doctors/Clinics -> Book Appointment -> View Results -> Chat with AI.

#### Registration
- **Endpoint**: `POST /users/register/user`
- **Request**:
```json
{
  "email": "patient@example.com",
  "phone": "01234567890",
  "full_name": "John Doe",
  "password": "strongpassword",
  "profile": {
    "blood_type": "O+",
    "height_cm": 180,
    "weight_kg": 75
  }
}
```

#### Authentication (Login)
- **Endpoint**: `POST /users/login`
- **Request**: `{"email": "patient@example.com", "password": "strongpassword"}`
- **Response**: Returns a JWT token and user profile details.

#### Booking an Appointment
- **Endpoint**: `POST /bookings/`
- **Request**:
```json
{
  "slot_id": "uuid-of-the-slot",
  "notes": "First time visit",
  "booking_source_id": "optional-source-uuid"
}
```

#### Rating a Booking
- **Endpoint**: `PATCH /bookings/{booking_id}/rate?rating=5`
- **Requirement**: Booking must be in `completed` status.

---

### B. Clinic
**Flow**: Register Clinic Account -> Manage Clinic Details -> Link Doctors -> Set Availability -> Generate Slots -> Manage Bookings.

#### Registration
- **Endpoint**: `POST /users/register/clinic`
- **Request**:
```json
{
  "email": "clinic@example.com",
  "phone": "0223456789",
  "full_name": "Main Admin",
  "password": "clinicpassword",
  "clinic": {
    "name": "Health First Clinic",
    "address": "123 Medical St",
    "phone": "0223456789",
    "email": "info@healthfirst.com"
  }
}
```

#### Clinic-Doctor Management
- **List Doctors**: `GET /clinics/{clinic_id}/doctors`
- **Link Doctor**: `POST /clinics/{clinic_id}/doctors/{doctor_id}`
- **Unlink Doctor**: `DELETE /clinics/{clinic_id}/doctors/{doctor_id}`
- **Clinic-Doctor Invitation**: See Section 3.

#### Slot Generation
- **Endpoint**: `POST /appointment-slots/generate`
- **Request**: `{"doctor_id": "...", "from_date": "2026-06-01", "to_date": "2026-06-07"}`

---

### C. Doctor
**Flow**: Register -> Manage Profile -> Set Availability -> View Appointments -> Manage Patient Records.

#### Registration
- **Endpoint**: `POST /users/register/doctor`
- **Request**: Includes specialization, experience, and license details.

#### Availability & Slots
- **Set Availability**: `POST /doctors/{doctor_id}/availability/`
- **List My Slots**: `GET /appointment-slots/?doctor_id=...`

---

## 3. Core Features Workflows

### Booking Lifecycle
1. **Created**: Status is `pending`.
2. **Confirmed**: Clinic/Doctor confirms via `PATCH /bookings/{id}/confirm`.
3. **Completed**: After the visit, status set via `PATCH /bookings/{id}/complete`.
4. **Cancelled**: Either party can cancel via `PATCH /bookings/{id}/cancel`.

### AI Diagnostics
- **Diabetes Analysis**: `POST /analysis/run`
- **Radiology (X-Ray)**: `POST /xray/upload` (Returns diagnosis and confidence).
- **History**: Results are automatically appended to the patient's **Medical Record**.

### Medical Records
- **Patient Access**: `GET /records/me`
- **Doctor Access**: `GET /records/user/{user_id}` (Authorized doctors only).

### AI Chat
- **Start Session**: `POST /chat/sessions`
- **Message Exchange**: `POST /chat/sessions/{id}/messages`

### Clinic-Doctor Invitation Flow
1. **Search Doctors**: `GET /clinics/search/doctors?specialization_id=...`
2. **Send Invitation**: `POST /clinics/{clinic_id}/invitations`
3. **Doctor Views Invitations**: `GET /doctors/me/invitations`
4. **Doctor Responds**: `PATCH /doctors/me/invitations/{id}/respond?accept=true`

---

## 4. Administrative Features (RBAC & Audit)
Admin users have access to system-wide logs and role management.
- **Audit Logs**: `GET /audit/` (Filter by user, clinic, or action).
- **Role Management**: `GET /roles/`, `POST /roles/assign`.
- **Specializations**: `POST /specializations/` (Add new medical fields).

---

## 5. Security & RBAC
The system uses **JWT (JSON Web Tokens)** for authentication.
- **Header**: `Authorization: Bearer <token>`
- **Cookie**: `access_token`
- **Permissions**: Each endpoint is protected based on roles (`admin`, `doctor`, `clinic`, `user`).

---

## 6. Development & Testing
- **API Docs**: Access `/docs` (Swagger) for the full, interactive list of all 50+ endpoints.
- **Database**: PostgreSQL (SQLAlchemy models in `models.py`).
- **Automation**: Integration tests available in `test_automation.py`.
