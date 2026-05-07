# 📋 Full Backend API Documentation — Frontend Integration Guide

> **Base URL**: `http://localhost:8000`
> **Auth**: Bearer token via `Authorization: Bearer <token>` header
> **Content-Type**: `application/json` (except file uploads)

---

## Table of Contents

1. [Authentication & How It Works](#1-authentication)
2. [Global Enums](#2-global-enums)
3. [Users Module](#3-users-module) — Registration, Login, Profile, Admin ops
4. [Specializations Module](#4-specializations-module)
5. [Doctors Module](#5-doctors-module) — CRUD, Invitations
6. [Clinics Module](#6-clinics-module) — CRUD, Doctor linking, Invitations
7. [Availability Module](#7-availability-module)
8. [Slots Module](#8-slots-module)
9. [Bookings Module](#9-bookings-module) — Full lifecycle
10. [Medical Records Module](#10-medical-records-module)
11. [AI Diagnostics Module](#11-ai-diagnostics-module) — Diabetes analysis
12. [X-Ray Module](#12-xray-module) — Radiology upload
13. [Chat Module](#13-chat-module) — AI chat sessions
14. [Roles Module](#14-roles-module) — RBAC
15. [Audit Module](#15-audit-module)
16. [Full System Flow](#16-full-system-flow)
17. [CRUD Summary Table](#17-crud-summary-table)

---

## 1. Authentication

### How It Works

1. User registers via one of the `/users/register/*` endpoints.
2. User logs in via `POST /users/login` → receives a JWT `access_token`.
3. Frontend stores the token and sends it on every request as:
   ```
   Authorization: Bearer <access_token>
   ```
4. Token expires after **30 minutes**. On `401`, redirect to login.
5. The login response also sets an `access_token` httpOnly cookie (for SSR/fallback).

### Roles

| Role     | Value      | Description                          |
|----------|------------|--------------------------------------|
| User     | `"user"`   | Patient. Can book, rate, use AI.     |
| Clinic   | `"clinic"` | Clinic owner. Manages doctors/slots. |
| Doctor   | `"doctor"` | Doctor. Manages own availability.    |
| Admin    | `"admin"`  | Full system access.                  |

---

## 2. Global Enums

These string enums appear in request/response bodies. Always send the **exact string value**.

| Enum Name              | Values                                          | Used In                    |
|------------------------|------------------------------------------------|----------------------------|
| `LanguageEnum`         | `"en"`, `"ar"`                                  | User preferences           |
| `RoleEnum`             | `"user"`, `"clinic"`, `"admin"`, `"doctor"`     | User role                  |
| `GenderEnum`           | `"male"`, `"female"`, `"other"`                 | User profile               |
| `LanguageSpokenEnum`   | `"en"`, `"ar"`, `"both"`                        | Doctor                     |
| `SlotStatusEnum`       | `"available"`, `"blocked"`, `"cancelled"`, `"booked"` | Appointment slots    |
| `BookingStatusEnum`    | `"pending"`, `"confirmed"`, `"completed"`, `"cancelled"` | Bookings          |
| `InvitationStatusEnum` | `"pending"`, `"accepted"`, `"rejected"`, `"expired"` | Clinic invitations    |
| `SeverityEnum`         | `"mild"`, `"moderate"`, `"severe"`              | Radiology findings         |
| `ViewPositionEnum`     | `"PA"`, `"AP"`, `"LAT"`                         | Radiology                  |
| `DataQualityEnum`      | `"good"`, `"fair"`, `"poor"`                    | Profile / Radiology        |
| `ActionTypeEnum`       | `"create"`, `"update"`, `"delete"`, `"login"`, `"logout"` | Audit logs        |

---

## 3. Users Module

**Prefix**: `/users`

### 3.1 `POST /users/register/user`

**Purpose**: Register a new patient account.
**Auth**: None (public).
**Status**: `201 Created`

**Request Body** — `UserRegister`:
```json
{
  "email": "patient@example.com",       // required, valid email
  "phone": "01012345678",               // required, unique
  "full_name": "John Doe",             // required
  "password": "SecurePass123!",         // required
  "language_preference": "en",          // optional, default "en"
  "profile": {                          // optional
    "date_of_birth": "1995-06-15",
    "gender": "male",
    "blood_type": "A+",
    "height_cm": 178.0,
    "weight_kg": 75.0,
    "known_allergies": "None",
    "chronic_conditions": "None",
    "emergency_contact_name": "Jane Doe",
    "emergency_contact_phone": "01098765432"
  }
}
```

**Response** — `UserWithProfileOut`:
```json
{
  "uuid": "a1b2c3d4-...",
  "email": "patient@example.com",
  "phone": "01012345678",
  "full_name": "John Doe",
  "language_preference": "en",
  "role": "user",
  "is_active": true,
  "created_at": "2026-05-07T10:00:00",
  "updated_at": null,
  "profile": {
    "id": "p1p2p3-...",
    "user_id": "a1b2c3d4-...",
    "date_of_birth": "1995-06-15",
    "gender": "male",
    "blood_type": "A+",
    "height_cm": 178.0,
    "weight_kg": 75.0,
    "known_allergies": "None",
    "chronic_conditions": "None",
    "emergency_contact_name": "Jane Doe",
    "emergency_contact_phone": "01098765432",
    "image_path": null,
    "data_quality_flag": null,
    "updated_at": null,
    "deleted_at": null
  }
}
```

**Errors**: `400` — Email or phone already registered.

---

### 3.2 `POST /users/register/clinic`

**Purpose**: Register a new clinic account. Creates both a user (role=clinic) and a clinic record.
**Auth**: None (public).
**Status**: `201 Created`

**Request Body** — `ClinicRegister`:
```json
{
  "email": "clinic@example.com",
  "phone": "01122334455",
  "full_name": "Elite Clinic Owner",
  "password": "SecurePass123!",
  "language_preference": "en",
  "clinic": {
    "name": "Elite Medical Center",
    "address": "Downtown Cairo",
    "phone": "0223456789",
    "email": "clinic@example.com",
    "location": "30.0444,31.2357"
  }
}
```

**Response** — `UserWithClinicOut`:
```json
{
  "uuid": "...",
  "email": "clinic@example.com",
  "phone": "01122334455",
  "full_name": "Elite Clinic Owner",
  "language_preference": "en",
  "role": "clinic",
  "is_active": true,
  "created_at": "...",
  "updated_at": null,
  "clinic_account": {
    "id": "clinic-uuid-...",
    "user_id": "...",
    "name": "Elite Medical Center",
    "address": "Downtown Cairo",
    "phone": "0223456789",
    "email": "clinic@example.com",
    "location": "30.0444,31.2357",
    "created_at": "...",
    "updated_at": null,
    "deleted_at": null
  }
}
```

---

### 3.3 `POST /users/register/doctor`

**Purpose**: Register an independent doctor account. No clinic assigned at registration.
**Auth**: None (public).
**Status**: `201 Created`

**Request Body** — `DoctorRegister`:
```json
{
  "email": "doctor@example.com",
  "phone": "01233445566",
  "full_name": "Dr. Ahmed",
  "password": "SecurePass123!",
  "language_preference": "en",
  "specialization_id": "spec-uuid-or-null",
  "language_spoken": "both",
  "bio_en": "Cardiologist with 10 years experience",
  "bio_ar": "طبيب قلب بخبرة ١٠ سنوات",
  "consultation_price_egp": 350.0,
  "years_of_experience": 10,
  "license_number": "EG-12345"
}
```

**Response** — `UserWithDoctorOut`:
```json
{
  "uuid": "...",
  "email": "doctor@example.com",
  "role": "doctor",
  "is_active": true,
  "doctor_account": {
    "id": "doctor-uuid-...",
    "user_id": "...",
    "full_name": "Dr. Ahmed",
    "specialization_id": "...",
    "language_spoken": "both",
    "bio_en": "...",
    "bio_ar": "...",
    "consultation_price_egp": 350.0,
    "years_of_experience": 10,
    "license_number": "EG-12345",
    "is_active": true,
    "is_verified": false,
    "average_rating": null,
    "rating_count": null,
    "created_at": "...",
    "specialization": null
  }
}
```

---

### 3.4 `POST /users/login`

**Purpose**: Authenticate any user (patient, clinic, doctor, admin) and get a JWT token.
**Auth**: None.

**Request Body** — `UserLogin`:
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!"
}
```

**Response** — `TokenOut`:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "user": { /* UserWithProfileOut OR UserWithClinicOut OR UserWithDoctorOut depending on role */ }
}
```

The `user` field shape depends on the user's role:
- `role = "user"` → includes `profile` (nullable)
- `role = "clinic"` → includes `clinic_account` (nullable)
- `role = "doctor"` → includes `doctor_account` (nullable)

**Errors**: `401` — Invalid credentials. `403` — Account deactivated or deleted.

---

### 3.5 `POST /users/logout`

**Purpose**: Clear the auth cookie. Frontend should also discard the stored token.
**Auth**: None (cookie-based).
**Response**: `{"message": "Logged out"}`

---

### 3.6 `GET /users/me`

**Purpose**: Get the currently authenticated user's full profile.
**Auth**: Required (any role).

**Response**: `UserWithProfileOut` | `UserWithClinicOut` | `UserWithDoctorOut` (based on role).

**When to use**: Call this on app startup / page refresh to load the current user's data.

---

### 3.7 `PUT /users/me`

**Purpose**: Update the current user's basic account info (name, phone, password, language).
**Auth**: Required (any role).

**Request Body** — `UserUpdate` (all fields optional, send only what changed):
```json
{
  "phone": "01099887766",
  "full_name": "New Name",
  "password": "NewPassword123!",
  "language_preference": "ar"
}
```

**Response**: Updated user object (same shape as `GET /users/me`).

---

### 3.8 `DELETE /users/me`

**Purpose**: Soft-delete the current user's own account. Sets `deleted_at` timestamp.
**Auth**: Required (any role).
**Response**: `{"message": "Account deleted"}`

---

### 3.9 `GET /users/me/profile`

**Purpose**: Get the patient profile (health data) for the current user.
**Auth**: Required, role must be `"user"`.
**Response** — `UserProfileOut`.
**Errors**: `403` if not a regular user. `404` if profile not found.

---

### 3.10 `POST /users/me/profile`

**Purpose**: Create a patient profile if one doesn't exist yet (e.g., user registered without profile data).
**Auth**: Required, role must be `"user"`.
**Status**: `201 Created`

**Request Body** — `UserProfileCreate`:
```json
{
  "date_of_birth": "1995-06-15",
  "gender": "male",
  "blood_type": "A+",
  "height_cm": 178.0,
  "weight_kg": 75.0,
  "known_allergies": "Penicillin",
  "chronic_conditions": "None",
  "emergency_contact_name": "Jane",
  "emergency_contact_phone": "01098765432"
}
```

**Errors**: `400` if profile already exists (use PATCH to update).

---

### 3.11 `PATCH /users/me/profile`

**Purpose**: Partially update the patient profile.
**Auth**: Required, role must be `"user"`.

**Request Body** — `UserProfileUpdate` (send only changed fields):
```json
{
  "weight_kg": 80.0,
  "image_path": "/uploads/avatar.jpg"
}
```

---

### 3.12 `GET /users/me/clinic`

**Purpose**: Get clinic details for the currently logged-in clinic account.
**Auth**: Required, role must be `"clinic"`.
**Response** — `ClinicOut`.

---

### 3.13 `PATCH /users/me/clinic`

**Purpose**: Update clinic details (name, address, phone, etc.).
**Auth**: Required, role must be `"clinic"`.

**Request Body** — `ClinicUpdate` (send only changed fields):
```json
{
  "name": "New Clinic Name",
  "address": "New Address",
  "phone": "0221112233",
  "email": "new@clinic.com",
  "location": "30.05,31.23"
}
```

---

### 3.14 `GET /users/` (Admin)

**Purpose**: List all non-deleted users in the system.
**Auth**: Required, **admin only**.
**Response**: Array of user objects.

---

### 3.15 `GET /users/{user_id}` (Admin)

**Purpose**: Get a specific user by UUID.
**Auth**: Required, **admin only**.
**Errors**: `404` if user not found.

---

### 3.16 `PATCH /users/{user_id}/role` (Admin)

**Purpose**: Change a user's role (e.g., promote to admin).
**Auth**: Required, **admin only**.
**Query Param**: `role` — one of `"user"`, `"clinic"`, `"admin"`, `"doctor"`.

---

### 3.17 `PATCH /users/{user_id}/switch` (Admin)

**Purpose**: Toggle a user's `is_active` status (activate/deactivate account).
**Auth**: Required, **admin only**.
**Response**: Updated user object.

---

### 3.18 `DELETE /users/{user_id}` (Admin)

**Purpose**: Soft-delete a user by UUID.
**Auth**: Required, **admin only**.
**Response**: `{"message": "User deleted"}`

---

## 4. Specializations Module

**Prefix**: `/specializations`

Specializations are medical categories (e.g., Cardiology, Dermatology). They are referenced by doctors.

### 4.1 `GET /specializations/`

**Purpose**: List all active specializations. Used to populate dropdown menus for searching doctors.
**Auth**: None (public).

**Response** — Array of `SpecializationOut`:
```json
[
  {
    "id": "spec-uuid-...",
    "name_en": "Cardiology",
    "name_ar": "أمراض القلب",
    "description_en": "Heart and blood vessel diseases",
    "description_ar": "أمراض القلب والأوعية الدموية",
    "created_at": "...",
    "updated_at": null
  }
]
```

### 4.2 `GET /specializations/{id}`

**Purpose**: Get a single specialization by ID.
**Auth**: None (public).
**Errors**: `404` if not found.

### 4.3 `POST /specializations/`

**Purpose**: Create a new specialization.
**Auth**: **Admin only**.
**Status**: `201 Created`

**Request Body** — `SpecializationCreate`:
```json
{
  "name_en": "Dermatology",
  "name_ar": "الأمراض الجلدية",
  "description_en": "Skin conditions",
  "description_ar": "أمراض الجلد"
}
```

### 4.4 `PUT /specializations/{id}`

**Purpose**: Update a specialization.
**Auth**: **Admin only**.

**Request Body** — `SpecializationUpdate` (all optional):
```json
{
  "name_en": "Updated Name",
  "description_en": "Updated description"
}
```

### 4.5 `DELETE /specializations/{id}`

**Purpose**: Soft-delete a specialization.
**Auth**: **Admin only**.
**Status**: `204 No Content`

---

## 5. Doctors Module

**Prefix**: `/doctors`

### 5.1 `GET /doctors/`

**Purpose**: List all active doctors. Used for browse/search on patient-facing pages.
**Auth**: None (public).

**Response** — Array of `DoctorOut`:
```json
[
  {
    "id": "doctor-uuid-...",
    "user_id": "...",
    "full_name": "Dr. Ahmed",
    "specialization_id": "spec-uuid-...",
    "language_spoken": "both",
    "bio_en": "Cardiologist...",
    "bio_ar": "طبيب قلب...",
    "consultation_price_egp": 350.0,
    "years_of_experience": 10,
    "license_number": "EG-12345",
    "is_active": true,
    "is_verified": false,
    "average_rating": 4.5,
    "rating_count": 12,
    "created_at": "...",
    "updated_at": null,
    "deleted_at": null,
    "specialization": {
      "id": "spec-uuid-...",
      "name_en": "Cardiology",
      "name_ar": "أمراض القلب",
      "description_en": "...",
      "description_ar": "...",
      "created_at": "...",
      "updated_at": null
    }
  }
]
```

### 5.2 `GET /doctors/{id}`

**Purpose**: Get a specific doctor's full details. Used for the doctor profile page.
**Auth**: None (public).
**Errors**: `404` if doctor not found.

### 5.3 `POST /doctors/`

**Purpose**: Create a doctor record (used by a clinic to add a doctor under their account).
**Auth**: Required, role must be `"clinic"`.
**Status**: `201 Created`

**Request Body** — `DoctorCreate`:
```json
{
  "full_name": "Dr. New Doctor",
  "specialization_id": "spec-uuid-...",
  "language_spoken": "en",
  "bio_en": "Specialist in...",
  "bio_ar": "متخصص في...",
  "consultation_price_egp": 300.0,
  "years_of_experience": 5,
  "license_number": "EG-99999",
  "is_active": true
}
```

> **Note**: This also creates a `DoctorClinic` junction record linking the new doctor to the clinic.

### 5.4 `PUT /doctors/{id}`

**Purpose**: Update doctor details.
**Auth**: Required, `"clinic"` (must own the doctor) or `"admin"`.

**Request Body** — `DoctorUpdate` (all optional):
```json
{
  "bio_en": "Updated bio",
  "consultation_price_egp": 400.0,
  "years_of_experience": 12,
  "is_active": true
}
```

### 5.5 `DELETE /doctors/{id}`

**Purpose**: Soft-delete a doctor.
**Auth**: Required, `"clinic"` (must own the doctor) or `"admin"`.
**Status**: `204 No Content`

### 5.6 `GET /doctors/me/invitations`

**Purpose**: List clinic invitations sent to the currently logged-in doctor.
**Auth**: Required, role must be `"doctor"`.
**Query Param**: `status` (optional) — `"pending"`, `"accepted"`, `"rejected"`, `"expired"`.

**Response** — Array of `InvitationOut`:
```json
[
  {
    "id": "inv-uuid-...",
    "clinic_id": "clinic-uuid-...",
    "doctor_id": "doctor-uuid-...",
    "status": "pending",
    "message": "Join Elite Center",
    "created_at": "...",
    "responded_at": null
  }
]
```

### 5.7 `PATCH /doctors/me/invitations/{invitation_id}/respond`

**Purpose**: Accept or reject a clinic invitation.
**Auth**: Required, role must be `"doctor"`.
**Query Param**: `accept` — `true` or `false`.

If accepted, a `DoctorClinic` junction record is created (doctor becomes linked to the clinic).

**Response**: `{"message": "Invitation accepted"}` or `{"message": "Invitation rejected"}`

---

## 6. Clinics Module

**Prefix**: `/clinics`

### 6.1 `GET /clinics/`

**Purpose**: List all active clinics. Used for browse/search pages.
**Auth**: None (public).
**Response** — Array of `ClinicOut`.

### 6.2 `GET /clinics/{clinic_id}`

**Purpose**: Get clinic details by ID.
**Auth**: None (public).
**Errors**: `404` if not found.

### 6.3 `GET /clinics/search/doctors`

**Purpose**: Search for doctors, optionally filtered by specialization.
**Auth**: None (public).
**Query Params**:
- `specialization_id` (optional) — Filter by specialization UUID.
- `city` (optional) — Filter by city (not yet implemented in backend).

**Response** — Array of `DoctorOut`.

**When to use**: On the patient search page to find doctors by specialty.

### 6.4 `GET /clinics/{clinic_id}/doctors`

**Purpose**: List all active doctors working at a specific clinic.
**Auth**: None (public).
**Response** — Array of `DoctorOut`.

### 6.5 `POST /clinics/{clinic_id}/doctors/{doctor_id}`

**Purpose**: Directly link a doctor to a clinic (without invitation flow).
**Auth**: Required, `"clinic"` (must own the clinic) or `"admin"`.
**Status**: `201 Created`
**Response**: `{"message": "Doctor linked to clinic successfully"}`

**Errors**: `400` if already linked. `403` if not authorized.

### 6.6 `DELETE /clinics/{clinic_id}/doctors/{doctor_id}`

**Purpose**: Unlink a doctor from a clinic (soft: sets `is_active=false`, records `left_at`).
**Auth**: Required, `"clinic"` (must own the clinic) or `"admin"`.
**Response**: `{"message": "Doctor unlinked from clinic"}`

### 6.7 `POST /clinics/{clinic_id}/invitations`

**Purpose**: Send an invitation from a clinic to a doctor asking them to join.
**Auth**: Required, `"clinic"` (must own the clinic) or `"admin"`.
**Status**: `201 Created`

**Request Body** — `InvitationCreate`:
```json
{
  "doctor_id": "doctor-uuid-...",
  "message": "We'd love to have you join our clinic!"
}
```

**Response** — `InvitationOut`.

**Errors**: `400` if doctor already linked or pending invitation exists. `404` if doctor not found.

---

## 7. Availability Module

**Prefix**: `/doctors/{doctor_id}/availability`

Availability rules define a doctor's **recurring weekly schedule**. They are templates used to generate concrete appointment slots.

### 7.1 `GET /doctors/{doctor_id}/availability/`

**Purpose**: List all availability rules for a specific doctor.
**Auth**: None (public).
**Query Param**: `is_active` (optional, boolean) — filter by active status.

**Response** — Array of `AvailabilityOut`:
```json
[
  {
    "id": "avail-uuid-...",
    "doctor_id": "doctor-uuid-...",
    "clinic_id": null,
    "day_of_week": 0,
    "start_time": "09:00:00",
    "end_time": "12:00:00",
    "slot_duration_minutes": 30,
    "is_active": true,
    "created_at": "...",
    "updated_at": null
  }
]
```

**`day_of_week` mapping**: `0`=Monday, `1`=Tuesday, `2`=Wednesday, `3`=Thursday, `4`=Friday, `5`=Saturday, `6`=Sunday.

### 7.2 `POST /doctors/{doctor_id}/availability/`

**Purpose**: Create a new availability rule for a doctor.
**Auth**: Required, `"clinic"`, `"admin"`, or `"doctor"` (only for own schedule).
**Status**: `201 Created`

**Request Body** — `AvailabilityCreate`:
```json
{
  "clinic_id": null,
  "day_of_week": 0,
  "start_time": "09:00:00",
  "end_time": "12:00:00",
  "slot_duration_minutes": 30
}
```

- `clinic_id`: Set to `null` for independent doctors. Set to a clinic UUID if the doctor works at that clinic.
- `day_of_week`: 0–6 (Monday–Sunday).
- `slot_duration_minutes`: Duration of each generated slot in minutes.

**Validation**: `end_time` must be > `start_time`. No duplicate rules for same day/time.

### 7.3 `PATCH /doctors/{doctor_id}/availability/{avail_id}`

**Purpose**: Update an existing availability rule.
**Auth**: Required, `"clinic"` or `"admin"`.

**Request Body** — `AvailabilityUpdate` (all optional):
```json
{
  "start_time": "10:00:00",
  "end_time": "13:00:00",
  "slot_duration_minutes": 20,
  "is_active": false
}
```

### 7.4 `DELETE /doctors/{doctor_id}/availability/{avail_id}`

**Purpose**: Hard-delete an availability rule.
**Auth**: Required, `"clinic"` or `"admin"`.
**Response**: `{"message": "Availability rule deleted"}`

---

## 8. Slots Module

**Prefix**: `/appointment-slots`

Slots are **concrete, bookable time windows** generated from availability rules. A patient selects a slot to create a booking.

### 8.1 `GET /appointment-slots/`

**Purpose**: List available slots for a specific doctor. This is the primary endpoint patients use to see bookable times.
**Auth**: None (public).
**Query Params** (all required/optional as noted):
- `doctor_id` (required) — UUID of the doctor.
- `from_date` (optional) — Filter slots from this date (YYYY-MM-DD).
- `to_date` (optional) — Filter slots up to this date.
- `slot_status` (optional, default `"available"`) — Filter by status.

**Response** — Array of `SlotOut`:
```json
[
  {
    "id": "slot-uuid-...",
    "doctor_id": "doctor-uuid-...",
    "clinic_id": "clinic-uuid-or-null",
    "availability_id": "avail-uuid-...",
    "slot_date": "2026-11-02",
    "slot_start_time": "09:00:00",
    "slot_end_time": "09:30:00",
    "slot_status": "available",
    "created_at": "...",
    "updated_at": null
  }
]
```

### 8.2 `GET /appointment-slots/{slot_id}`

**Purpose**: Get details of a single slot.
**Auth**: Required (any role).
**Errors**: `404` if not found.

### 8.3 `POST /appointment-slots/generate`

**Purpose**: Bulk-generate slots from a doctor's availability rules for a date range. This is the **key setup step** after creating availability rules.
**Auth**: Required, `"clinic"`, `"admin"`, or `"doctor"` (only for own slots).

**Request Body** — `SlotGenerateRequest`:
```json
{
  "doctor_id": "doctor-uuid-...",
  "clinic_id": null,
  "from_date": "2026-11-02",
  "to_date": "2026-11-08"
}
```

- `clinic_id`: Set to `null` for independent doctors. Set to a clinic UUID to generate only for that clinic's rules.
- Max range: **90 days**.

**Response** — `SlotGenerationResponse`:
```json
{
  "generated": 12,
  "skipped": 0,
  "slots": [ /* array of SlotOut objects */ ]
}
```

- `generated`: Number of new slots created.
- `skipped`: Number of slots that already existed (duplicates avoided).

**When to use**: After creating availability rules, call this to materialize actual bookable slots.

### 8.4 `POST /appointment-slots/`

**Purpose**: Manually create a single slot (instead of bulk generation).
**Auth**: Required, `"clinic"` or `"admin"`.
**Status**: `201 Created`

**Request Body** — `SlotCreate`:
```json
{
  "availability_id": "avail-uuid-...",
  "slot_date": "2026-11-05",
  "slot_start_time": "14:00:00",
  "slot_end_time": "14:30:00"
}
```

### 8.5 `PATCH /appointment-slots/{slot_id}`

**Purpose**: Update a slot's status (e.g., block it, cancel it).
**Auth**: Required, `"clinic"`, `"doctor"`, or `"admin"`.

**Request Body** — `SlotStatusUpdate`:
```json
{
  "slot_status": "blocked",
  "notes": "Doctor unavailable"
}
```

**Business Rule**: Cannot change a `"booked"` slot back to `"available"` (use cancel booking instead).

### 8.6 `DELETE /appointment-slots/{slot_id}`

**Purpose**: Hard-delete a slot.
**Auth**: Required, **admin only**.
**Business Rule**: Cannot delete a `"booked"` slot.
**Response**: `{"message": "Slot deleted"}`

---

## 9. Bookings Module

**Prefix**: `/bookings`

### Booking Lifecycle State Machine

```
pending → confirmed → completed
   ↓         ↓
cancelled  cancelled
```

- **pending**: Patient created the booking. Waiting for clinic/doctor confirmation.
- **confirmed**: Clinic or doctor approved the booking.
- **completed**: Appointment finished. Patient can now rate.
- **cancelled**: Cancelled by patient, clinic, or doctor. Slot becomes available again.

### 9.1 `POST /bookings/`

**Purpose**: Create a new booking for an available slot. This is how a patient books an appointment.
**Auth**: Required (any authenticated user, typically `"user"`).
**Status**: `201 Created`

**Request Body** — `BookingCreate`:
```json
{
  "slot_id": "slot-uuid-...",
  "notes": "First visit, chest pain",
  "booking_language": "ar",
  "booking_source_id": null
}
```

**Side Effects**:
- The slot's status changes from `"available"` → `"booked"`.
- The booking starts in `"pending"` status.

**Response** — `BookingOut`:
```json
{
  "id": "booking-uuid-...",
  "user_id": "patient-uuid-...",
  "doctor_id": "doctor-uuid-...",
  "clinic_id": "clinic-uuid-or-null",
  "slot": {
    "id": "slot-uuid-...",
    "slot_date": "2026-11-02",
    "slot_start_time": "09:00:00",
    "slot_end_time": "09:30:00"
  },
  "doctor": {
    "id": "doctor-uuid-...",
    "full_name": "Dr. Ahmed"
  },
  "clinic": {
    "id": "clinic-uuid-...",
    "name": "Elite Medical Center",
    "address": "Downtown"
  },
  "booking_status": "pending",
  "payment_reference": null,
  "payment_status": null,
  "cancellation_reason": null,
  "created_at": "...",
  "updated_at": null,
  "deleted_at": null
}
```

**Errors**:
- `404` — Slot not found.
- `409` — Slot not available OR user already has a booking for this doctor on that date.

### 9.2 `GET /bookings/me`

**Purpose**: Get the current patient's bookings with optional filters.
**Auth**: Required (any authenticated user).
**Query Params** (all optional):
- `booking_status` — `"pending"`, `"confirmed"`, `"completed"`, `"cancelled"`
- `from_date` / `to_date` — Date range filter (YYYY-MM-DD).
- `doctor_id` — Filter by specific doctor.

**Response** — Array of `BookingOut`.

### 9.3 `GET /bookings/doctor/me`

**Purpose**: Get bookings for the logged-in doctor or clinic's doctors.
**Auth**: Required, `"clinic"` or `"doctor"`.
**Query Params** (all optional): same as 9.2 + `doctor_id`.

**When to use**: Doctor dashboard to see upcoming appointments. Clinic dashboard to see all clinic bookings.

### 9.4 `GET /bookings/`

**Purpose**: List all bookings in the system (admin view).
**Auth**: Required, **admin only**.
**Query Params** (all optional): `user_id`, `doctor_id`, `clinic_id`, `booking_status`, `from_date`, `to_date`.

### 9.5 `GET /bookings/{booking_id}`

**Purpose**: Get full details of a specific booking.
**Auth**: Required. Patient can only see own bookings. Clinic/Doctor can only see their bookings. Admin can see all.

### 9.6 `PATCH /bookings/{booking_id}/confirm`

**Purpose**: Confirm a pending booking.
**Auth**: Required, `"clinic"`, `"doctor"`, or `"admin"`.
**Business Rule**: Only `"pending"` → `"confirmed"`.
**Response** — Updated `BookingOut`.

### 9.7 `PATCH /bookings/{booking_id}/complete`

**Purpose**: Mark a confirmed booking as completed (appointment done).
**Auth**: Required, `"clinic"`, `"doctor"`, or `"admin"`.
**Business Rule**: Only `"confirmed"` → `"completed"`.

### 9.8 `PATCH /bookings/{booking_id}/cancel`

**Purpose**: Cancel a booking. Can be called by patient, doctor, or clinic.
**Auth**: Required (owner check applies).
**Business Rule**: Cannot cancel a `"completed"` booking.
**Side Effect**: The associated slot's status reverts to `"available"`.
**Response**: `{"message": "Booking cancelled"}`

### 9.9 `PATCH /bookings/{booking_id}/reschedule`

**Purpose**: Move a booking to a different slot.
**Auth**: Required (owner check applies).

**Request Body** — `BookingReschedule`:
```json
{
  "new_slot_id": "new-slot-uuid-..."
}
```

**Side Effects**:
- Old slot → `"available"`.
- New slot → `"booked"`.
- Only works for `"pending"` or `"confirmed"` bookings.

### 9.10 `PATCH /bookings/{booking_id}/rate`

**Purpose**: Rate a completed booking (1–5 stars).
**Auth**: Required, must be the patient who booked.
**Query Param**: `rating` (required, integer 1–5).
**Business Rule**: Only `"completed"` bookings can be rated.
**Side Effect**: Updates the doctor's `average_rating` and `rating_count`.
**Response**: `{"message": "Rating submitted successfully"}`

### 9.11 `GET /bookings/{booking_id}/invoice`

**Purpose**: Generate an invoice summary for a booking.
**Auth**: Required (any authenticated user).

**Response**:
```json
{
  "invoice_id": "INV-a1b2c3d4",
  "booking_id": "booking-uuid-...",
  "amount": 500.0,
  "tax": 50.0,
  "total": 550.0,
  "pdf_url": "https://api.example.com/invoices/INV-a1b2c3d4.pdf"
}
```

---

## 10. Medical Records Module

**Prefix**: `/records`

Medical records are auto-updated JSON documents that aggregate a patient's diagnostic and radiology history.

### 10.1 `GET /records/me`

**Purpose**: Get the current user's medical record. Creates an empty one if none exists.
**Auth**: Required (any authenticated user).

**Response** — `MedicalRecordOut`:
```json
{
  "id": "record-uuid-...",
  "user_id": "patient-uuid-...",
  "record": {
    "diagnostics": [...],
    "radiology": [...]
  },
  "generated_at": "...",
  "record_types": []
}
```

### 10.2 `PATCH /records/me`

**Purpose**: Manually update the medical record content.
**Auth**: Required (any authenticated user).

**Request Body** — `MedicalRecordUpdate`:
```json
{
  "record": {
    "diagnostics": [...],
    "notes": "Additional medical notes"
  }
}
```

### 10.3 `GET /records/user/{user_id}`

**Purpose**: Get a specific patient's medical record (for doctors viewing their patient's record).
**Auth**: Required, `"doctor"` or `"admin"`.

---

## 11. AI Diagnostics Module

**Prefix**: `/analysis`

### 11.1 `POST /analysis/run`

**Purpose**: Run the diabetes risk prediction AI model. Saves the diagnostic record and auto-updates the patient's medical record.
**Auth**: Required (any authenticated user, typically `"user"`).

**Request Body** — `DiabetesRequest`:
```json
{
  "pregnancies": 0,
  "glucose": 110,
  "blood_pressure": 70,
  "skin_thickness": 20,
  "insulin": 0,
  "bmi": 24.5,
  "diabetes_pedigree_function": 0.4,
  "age": 28
}
```

All fields are **required**.

**Response**:
```json
{
  "prediction": 0,
  "confidence": 0.9
}
```

- `prediction`: `0` = No diabetes, `1` = Diabetes detected.
- `confidence`: Model confidence score (0–1).

**Side Effects**: Creates a `Diagnostic` + `DiagnosticResult` record. Auto-updates the patient's `MedicalRecord`.

---

## 12. X-Ray Module

**Prefix**: `/xray`

### 12.1 `POST /xray/upload`

**Purpose**: Upload a chest X-ray image for AI analysis. Saves the image, runs disease classification, and updates medical records.
**Auth**: Required (any authenticated user).
**Content-Type**: `multipart/form-data`

**Request**: File upload (form field name: `file`).
```
POST /xray/upload
Content-Type: multipart/form-data

file: <binary image data>
```

**Response** — `RadiologyOut`:
```json
{
  "id": "radiology-uuid-...",
  "user_id": "patient-uuid-...",
  "image_path": "uploads/xray_uuid_20260507_100000.jpg",
  "image_hash": null,
  "body_part": "chest",
  "view_position": null,
  "data_quality_flag": null,
  "uploaded_at": "...",
  "deleted_at": null,
  "findings": [
    {
      "id": "finding-uuid-...",
      "radiology_id": "radiology-uuid-...",
      "finding_name": "normal",
      "finding_range": null,
      "confidence_score": 0.92,
      "severity": null,
      "bounding_box": null,
      "created_at": "..."
    }
  ]
}
```

**Side Effects**: Saves image to `uploads/` directory. Creates `Radiology` + `RadiologyFinding` records. Auto-updates `MedicalRecord`.

---

## 13. Chat Module

**Prefix**: `/chat`

AI-powered chat sessions for symptom checking and medical guidance.

### 13.1 `POST /chat/sessions`

**Purpose**: Start a new AI chat session.
**Auth**: Required (any authenticated user).
**Status**: `201 Created`

**Request Body** — `ChatSessionCreate`:
```json
{
  "vendor_llm": "openai"
}
```

**Response** — `ChatSessionOut`:
```json
{
  "chat_session_id": "chat-uuid-...",
  "user_id": "patient-uuid-...",
  "session_id": null,
  "vendor_llm": "openai",
  "started_at": "...",
  "ended_at": null
}
```

### 13.2 `GET /chat/sessions`

**Purpose**: List all chat sessions for the current user.
**Auth**: Required.
**Response** — Array of `ChatSessionOut`.

### 13.3 `GET /chat/sessions/{session_id}`

**Purpose**: Get a specific chat session with messages.
**Auth**: Required (must own the session).
**Errors**: `404` if not found or not owned by current user.

### 13.4 `POST /chat/sessions/{session_id}/messages`

**Purpose**: Add a message to a chat session.
**Auth**: Required (must own the session).
**Status**: `201 Created`
**Query Params**:
- `content` (required) — The message text.
- `sender_role` (required) — `"user"` or `"assistant"`.

---

## 14. Roles Module (RBAC)

**Prefix**: `/roles`

Fine-grained role-based access control. All endpoints are **admin only**.

### 14.1 `GET /roles/`

**Purpose**: List all available roles.
**Auth**: **Admin only**.

**Response** — Array of `RoleOut`:
```json
[
  {
    "role_id": 1,
    "role_name_en": "user",
    "role_name_ar": "مستخدم",
    "description_en": "Regular patient user",
    "description_ar": "مستخدم عادي"
  }
]
```

### 14.2 `POST /roles/`

**Purpose**: Create a new role.
**Auth**: **Admin only**.
**Status**: `201 Created`

**Request Body** — `RoleCreate`:
```json
{
  "role_name_en": "moderator",
  "role_name_ar": "مشرف",
  "description_en": "Content moderator",
  "description_ar": "مشرف محتوى"
}
```

### 14.3 `POST /roles/assign`

**Purpose**: Assign a role to a user.
**Auth**: **Admin only**.
**Query Params**: `user_id` (string), `role_id` (integer).
**Response**: `{"message": "Role assigned successfully"}`

### 14.4 `DELETE /roles/unassign`

**Purpose**: Remove a role from a user.
**Auth**: **Admin only**.
**Query Params**: `user_id` (string), `role_id` (integer).
**Response**: `{"message": "Role unassigned successfully"}`

### 14.5 `GET /roles/user/{user_id}`

**Purpose**: Get all roles assigned to a specific user.
**Auth**: **Admin only**.
**Response** — Array of `UserRoleOut`.

---

## 15. Audit Module

**Prefix**: `/audit`

System audit trail. All endpoints are **admin only**.

### 15.1 `GET /audit/`

**Purpose**: List recent audit log entries (max 100).
**Auth**: **Admin only**.
**Query Params** (all optional):
- `user_id` — Filter by user.
- `clinic_id` — Filter by clinic.
- `action_type` — `"create"`, `"update"`, `"delete"`, `"login"`, `"logout"`.

**Response** — Array of `AuditLogOut`:
```json
[
  {
    "audit_id": "audit-uuid-...",
    "user_id": "...",
    "clinic_id": null,
    "action_type": "create",
    "resource_type": "booking",
    "resource_id": "booking-uuid-...",
    "ip_address": "192.168.1.1",
    "location": null,
    "old_values": null,
    "new_values": {"status": "pending"},
    "description": "Booking created",
    "created_at": "..."
  }
]
```

### 15.2 `GET /audit/{audit_id}`

**Purpose**: Get a specific audit log entry.
**Auth**: **Admin only**.
**Errors**: `404` if not found.

---

## 16. Full System Flow

This section describes the **complete end-to-end flow** matching the automation test script. Follow these steps in order.

### Phase 0 — Bootstrap (Admin Setup)

```
1. Run `python seed_db.py` to seed specializations and default roles.
2. Register an admin account via POST /users/register/user.
3. Run `python promote_admin.py <admin_email>` to promote to admin role.
4. Login as admin → save the token.
```

### Phase 1 — Identity Setup

Register all user accounts:

```
┌─────────────────────────────────────────────────────────────┐
│  POST /users/register/user    → Patient account             │
│  POST /users/register/clinic  → Clinic + Clinic owner       │
│  POST /users/register/doctor  → Doctor 1 (will join clinic) │
│  POST /users/register/doctor  → Doctor 2 (independent)      │
└─────────────────────────────────────────────────────────────┘
```

Then login each account to get their tokens:
```
POST /users/login  (for each account)
→ Save access_token for each role
```

### Phase 2 — Clinical Recruitment (Link Doctor to Clinic)

```
┌──────────────────────────────────────────────────────────────┐
│ 1. Clinic sends invitation:                                   │
│    POST /clinics/{clinic_id}/invitations                      │
│    Body: { "doctor_id": "...", "message": "Join us" }         │
│    Auth: Clinic token                                         │
│                                                               │
│ 2. Doctor accepts invitation:                                 │
│    PATCH /doctors/me/invitations/{inv_id}/respond?accept=true │
│    Auth: Doctor token                                         │
│                                                               │
│ Result: Doctor is now linked to the clinic (DoctorClinic row) │
└──────────────────────────────────────────────────────────────┘
```

### Phase 3 — Availability & Slot Setup

**For Clinic Doctor:**
```
1. Create availability rule:
   POST /doctors/{doctor_id}/availability/
   Auth: Doctor token
   Body: { "day_of_week": 0, "start_time": "09:00", "end_time": "10:00", "slot_duration_minutes": 30 }

2. Generate slots:
   POST /appointment-slots/generate
   Auth: Clinic token
   Body: { "doctor_id": "...", "from_date": "2026-11-02", "to_date": "2026-11-02" }

   → Returns generated slot IDs
```

**For Independent Doctor:**
```
1. Create availability rule:
   POST /doctors/{doctor_id}/availability/
   Auth: Doctor token
   Body: { "day_of_week": 0, "start_time": "14:00", "end_time": "15:00", "slot_duration_minutes": 30 }

2. Generate slots:
   POST /appointment-slots/generate
   Auth: Doctor token (independent doctors can generate their own)
   Body: { "doctor_id": "...", "from_date": "2026-11-02", "to_date": "2026-11-02" }
```

### Phase 4 — AI Services (Patient)

```
1. Diabetes Analysis:
   POST /analysis/run
   Auth: Patient token
   Body: { pregnancies, glucose, blood_pressure, ... }
   → Returns prediction (0/1) + confidence

2. X-Ray Upload:
   POST /xray/upload
   Auth: Patient token
   Content-Type: multipart/form-data
   Body: file=<image>
   → Returns findings (normal/pneumonia/covid) + confidence

Both auto-update the patient's Medical Record.
```

### Phase 5 — Booking Journey (Clinic Doctor)

```
┌────────────────────────────────────────────────────┐
│ Step 1: Patient creates booking                     │
│   POST /bookings/                                   │
│   Auth: Patient token                               │
│   Body: { "slot_id": "<clinic_slot_id>" }           │
│   → Status: PENDING                                 │
│                                                     │
│ Step 2: Clinic confirms booking                     │
│   PATCH /bookings/{id}/confirm                      │
│   Auth: Clinic token                                │
│   → Status: CONFIRMED                               │
│                                                     │
│ Step 3: Clinic completes booking                    │
│   PATCH /bookings/{id}/complete                     │
│   Auth: Clinic token                                │
│   → Status: COMPLETED                               │
│                                                     │
│ Step 4: Patient rates the booking                   │
│   PATCH /bookings/{id}/rate?rating=5                │
│   Auth: Patient token                               │
│   → Doctor's average_rating updated                 │
└────────────────────────────────────────────────────┘
```

### Phase 6 — Booking Journey (Independent Doctor)

```
Same flow as Phase 5, but:
- The slot has clinic_id = null
- Doctor (not clinic) confirms and completes
- Auth: Independent Doctor token for confirm/complete
```

### Phase 7 — Verification

```
1. Check Medical Record:
   GET /records/me  (Patient token)
   → Verify diagnostics and radiology are present

2. Check Audit Logs:
   GET /audit/  (Admin token)
   → Verify system events were logged
```

### Visual Flow Diagram

```
  Patient Register → Login → Search Doctor → View Slots → Book Slot
       ↓                                                       ↓
  Run AI Analysis                                    Booking (PENDING)
  Upload X-Ray                                             ↓
       ↓                                        Clinic/Doctor Confirms
  Medical Record Updated                               (CONFIRMED)
                                                           ↓
                                                 Appointment Happens
                                                       (COMPLETED)
                                                           ↓
                                                    Patient Rates (1-5)
                                                           ↓
                                                  Doctor Rating Updated
```

---

## 17. CRUD Summary Table

Every endpoint in the system at a glance:

| # | Method | Endpoint | Auth | Purpose |
|---|--------|----------|------|---------|
| 1 | `POST` | `/users/register/user` | Public | Register patient |
| 2 | `POST` | `/users/register/clinic` | Public | Register clinic |
| 3 | `POST` | `/users/register/doctor` | Public | Register doctor |
| 4 | `POST` | `/users/login` | Public | Login (get JWT) |
| 5 | `POST` | `/users/logout` | Public | Logout (clear cookie) |
| 6 | `GET` | `/users/me` | Any | Get current user |
| 7 | `PUT` | `/users/me` | Any | Update current user |
| 8 | `DELETE` | `/users/me` | Any | Soft-delete own account |
| 9 | `GET` | `/users/me/profile` | User | Get patient profile |
| 10 | `POST` | `/users/me/profile` | User | Create patient profile |
| 11 | `PATCH` | `/users/me/profile` | User | Update patient profile |
| 12 | `GET` | `/users/me/clinic` | Clinic | Get clinic details |
| 13 | `PATCH` | `/users/me/clinic` | Clinic | Update clinic details |
| 14 | `GET` | `/users/` | Admin | List all users |
| 15 | `GET` | `/users/{user_id}` | Admin | Get user by ID |
| 16 | `PATCH` | `/users/{user_id}/role` | Admin | Change user role |
| 17 | `PATCH` | `/users/{user_id}/switch` | Admin | Toggle active status |
| 18 | `DELETE` | `/users/{user_id}` | Admin | Soft-delete user |
| 19 | `GET` | `/specializations/` | Public | List specializations |
| 20 | `GET` | `/specializations/{id}` | Public | Get specialization |
| 21 | `POST` | `/specializations/` | Admin | Create specialization |
| 22 | `PUT` | `/specializations/{id}` | Admin | Update specialization |
| 23 | `DELETE` | `/specializations/{id}` | Admin | Delete specialization |
| 24 | `GET` | `/doctors/` | Public | List all doctors |
| 25 | `GET` | `/doctors/{id}` | Public | Get doctor details |
| 26 | `POST` | `/doctors/` | Clinic | Create doctor record |
| 27 | `PUT` | `/doctors/{id}` | Clinic/Admin | Update doctor |
| 28 | `DELETE` | `/doctors/{id}` | Clinic/Admin | Soft-delete doctor |
| 29 | `GET` | `/doctors/me/invitations` | Doctor | List my invitations |
| 30 | `PATCH` | `/doctors/me/invitations/{id}/respond` | Doctor | Accept/reject invitation |
| 31 | `GET` | `/clinics/` | Public | List all clinics |
| 32 | `GET` | `/clinics/{clinic_id}` | Public | Get clinic details |
| 33 | `GET` | `/clinics/search/doctors` | Public | Search doctors by specialty |
| 34 | `GET` | `/clinics/{clinic_id}/doctors` | Public | List clinic's doctors |
| 35 | `POST` | `/clinics/{id}/doctors/{id}` | Clinic/Admin | Link doctor to clinic |
| 36 | `DELETE` | `/clinics/{id}/doctors/{id}` | Clinic/Admin | Unlink doctor from clinic |
| 37 | `POST` | `/clinics/{id}/invitations` | Clinic/Admin | Send invitation to doctor |
| 38 | `GET` | `/doctors/{id}/availability/` | Public | List availability rules |
| 39 | `POST` | `/doctors/{id}/availability/` | Clinic/Admin/Doctor | Create availability rule |
| 40 | `PATCH` | `/doctors/{id}/availability/{id}` | Clinic/Admin | Update availability rule |
| 41 | `DELETE` | `/doctors/{id}/availability/{id}` | Clinic/Admin | Delete availability rule |
| 42 | `GET` | `/appointment-slots/` | Public | List slots for doctor |
| 43 | `GET` | `/appointment-slots/{id}` | Any | Get slot details |
| 44 | `POST` | `/appointment-slots/generate` | Clinic/Admin/Doctor | Bulk-generate slots |
| 45 | `POST` | `/appointment-slots/` | Clinic/Admin | Create single slot |
| 46 | `PATCH` | `/appointment-slots/{id}` | Clinic/Doctor/Admin | Update slot status |
| 47 | `DELETE` | `/appointment-slots/{id}` | Admin | Delete slot |
| 48 | `POST` | `/bookings/` | Any | Create booking |
| 49 | `GET` | `/bookings/me` | Any | My bookings |
| 50 | `GET` | `/bookings/doctor/me` | Clinic/Doctor | Doctor/clinic bookings |
| 51 | `GET` | `/bookings/` | Admin | All bookings |
| 52 | `GET` | `/bookings/{id}` | Any (ownership) | Booking details |
| 53 | `PATCH` | `/bookings/{id}/confirm` | Clinic/Doctor/Admin | Confirm booking |
| 54 | `PATCH` | `/bookings/{id}/complete` | Clinic/Doctor/Admin | Complete booking |
| 55 | `PATCH` | `/bookings/{id}/cancel` | Any (ownership) | Cancel booking |
| 56 | `PATCH` | `/bookings/{id}/reschedule` | Any (ownership) | Reschedule booking |
| 57 | `PATCH` | `/bookings/{id}/rate` | User (owner) | Rate completed booking |
| 58 | `GET` | `/bookings/{id}/invoice` | Any | Get invoice |
| 59 | `GET` | `/records/me` | Any | Get my medical record |
| 60 | `PATCH` | `/records/me` | Any | Update my medical record |
| 61 | `GET` | `/records/user/{user_id}` | Doctor/Admin | Get patient's record |
| 62 | `POST` | `/analysis/run` | Any | Run diabetes AI analysis |
| 63 | `POST` | `/xray/upload` | Any | Upload X-ray for AI |
| 64 | `POST` | `/chat/sessions` | Any | Create chat session |
| 65 | `GET` | `/chat/sessions` | Any | List my chat sessions |
| 66 | `GET` | `/chat/sessions/{id}` | Any (owner) | Get chat session |
| 67 | `POST` | `/chat/sessions/{id}/messages` | Any (owner) | Add chat message |
| 68 | `GET` | `/roles/` | Admin | List roles |
| 69 | `POST` | `/roles/` | Admin | Create role |
| 70 | `POST` | `/roles/assign` | Admin | Assign role to user |
| 71 | `DELETE` | `/roles/unassign` | Admin | Remove role from user |
| 72 | `GET` | `/roles/user/{user_id}` | Admin | Get user's roles |
| 73 | `GET` | `/audit/` | Admin | List audit logs |
| 74 | `GET` | `/audit/{audit_id}` | Admin | Get audit log entry |

---

> **Total: 74 endpoints** covering authentication, user management, clinical operations, scheduling, booking lifecycle, AI diagnostics, radiology, chat, RBAC, and audit logging.
