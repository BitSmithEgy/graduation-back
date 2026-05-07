# Medical System - Frontend Integration Guide

This guide is designed for the frontend team to integrate with the backend API. It focuses on the **User Journeys** and provides exact Request/Response examples for every step.

---

## 1. Authentication & Onboarding

### Flow: Registration
Users can register with one of three roles: `user` (Patient), `clinic`, or `doctor`.

#### A. Register Patient
- **Endpoint**: `POST /users/register/user`
- **Request**:
```json
{
  "email": "patient@example.com",
  "phone": "01012345678",
  "full_name": "John Doe",
  "password": "StrongPassword123!",
  "profile": {
    "blood_type": "O+",
    "height_cm": 180,
    "weight_kg": 85
  }
}
```

#### B. Register Clinic
- **Endpoint**: `POST /users/register/clinic`
- **Request**:
```json
{
  "email": "clinic@example.com",
  "phone": "0223456789",
  "full_name": "Clinic Manager",
  "password": "ClinicPassword123!",
  "clinic": {
    "name": "Healing Center",
    "address": "123 Medical Lane",
    "phone": "0223456789",
    "email": "contact@healing.com"
  }
}
```

#### C. Register Doctor
- **Endpoint**: `POST /users/register/doctor`
- **Request**:
```json
{
  "email": "doctor@example.com",
  "phone": "01234567891",
  "full_name": "Dr. Smith",
  "password": "DoctorPassword123!",
  "specialization_id": "uuid-from-specializations-list",
  "years_of_experience": 10
}
```

### Flow: Login
- **Endpoint**: `POST /users/login`
- **Request**: `{"email": "...", "password": "..."}`
- **Response**: Returns a `access_token` and the `user` object containing role-specific details (profile, clinic_account, or doctor_account).

---

## 2. Journey: Clinical Recruitment
Clinics must recruit doctors to generate clinic-based slots.

1.  **Search Doctors**: Clinic calls `GET /clinics/search/doctors?specialization_id=...` to find available doctors.
2.  **Invite**: Clinic calls `POST /clinics/{clinic_id}/invitations` with `doctor_id`.
3.  **Accept**: Doctor views invites at `GET /doctors/me/invitations` and accepts via:
    `PATCH /doctors/me/invitations/{id}/respond?accept=true`

---

## 3. Journey: Scheduling & Slot Generation
Doctors/Clinics must set availability before patients can book.

### Step 1: Set Availability Rule
- **Endpoint**: `POST /doctors/{doctor_id}/availability/`
- **Payload**:
```json
{
  "day_of_week": 0, 
  "start_time": "09:00:00",
  "end_time": "17:00:00",
  "slot_duration_minutes": 30
}
```
*Note: `day_of_week` is 0 (Monday) to 6 (Sunday).*

### Step 2: Generate Slots
- **Endpoint**: `POST /appointment-slots/generate`
- **Payload**: `{"doctor_id": "...", "from_date": "2026-10-01", "to_date": "2026-10-30"}`
- **Response**:
```json
{
  "generated": 10,
  "slots": [
    {"id": "slot-uuid", "slot_date": "2026-10-01", "slot_start_time": "09:00:00", ...}
  ]
}
```

---

## 4. Journey: Patient Booking Flow

1.  **Search Slots**: Patient calls `GET /appointment-slots/?doctor_id=...&slot_date=...` to see available times.
2.  **Book**: Patient calls `POST /bookings/` with `{"slot_id": "...", "notes": "Fever"}`.
3.  **Confirm**: Clinic or Doctor calls `PATCH /bookings/{id}/confirm`.
4.  **Complete**: After the visit, Clinic/Doctor calls `PATCH /bookings/{id}/complete`.
5.  **Rate**: Patient calls `PATCH /bookings/{id}/rate?rating=5`.

---

## 5. Journey: AI Health Services

### A. Diabetes Risk Analysis
- **Endpoint**: `POST /analysis/run`
- **Logic**: Patient enters vitals, backend returns prediction.
- **Request**:
```json
{
  "pregnancies": 1, "glucose": 85, "blood_pressure": 66, 
  "skin_thickness": 29, "insulin": 0, "bmi": 26.6, 
  "diabetes_pedigree_function": 0.35, "age": 31
}
```
- **Response**: `{"prediction": 0, "probability": 0.12}`

### B. X-Ray Diagnosis
- **Endpoint**: `POST /xray/upload`
- **Logic**: Upload image file, backend returns AI diagnosis.
- **Form Data**: `file: <image_binary>`
- **Response**: `{"diagnosis": "Normal", "confidence": 0.98}`

---

## 6. Medical Records & Chat

### Medical Record
- **Endpoint**: `GET /records/me`
- **Response**: A nested JSON object containing `vitals`, `diagnostics` (AI results), and `visits` (booking history).

### AI Medical Chat
1.  **Start Session**: `POST /chat/sessions` → returns `chat_session_id`.
2.  **Send Message**: `POST /chat/sessions/{id}/messages` with `{"message_content": "..."}`.
3.  **History**: `GET /chat/sessions/{id}/messages` to retrieve conversation.


---

## 7. Resource Discovery (Search & Browsing)

Before booking, patients need to discover entities.

### A. List Specializations
- **Endpoint**: `GET /specializations/`
- **Use**: Populates the "Select Specialty" dropdown.

### B. List Clinics
- **Endpoint**: `GET /clinics/`
- **Use**: Browsing all healthcare facilities.

### C. Get Entity Details
- **Doctor Profile**: `GET /doctors/{id}` (Includes bio, rating, and specialty).
- **Clinic Profile**: `GET /clinics/{id}` (Includes address and facility info).

---

## 8. Profile & Account Management

### A. Get Current User Details
- **Endpoint**: `GET /users/me`
- **Logic**: Use this on app startup to determine the user's role and populate the "My Account" page.

### B. Update Profile
- **Endpoint**: `PATCH /users/me`
- **Example (Patient)**:
```json
{
  "full_name": "Updated Name",
  "profile": {
    "weight_kg": 78.5
  }
}
```

### C. My Bookings (Patient/Doctor/Clinic)
- **Patient**: `GET /bookings/me`
- **Clinic/Doctor**: `GET /bookings/` (Filtered by role).

---

## Important Integration Notes
- **Headers**: All protected endpoints require `Authorization: Bearer <token>`.
- **Date Formats**: Use `YYYY-MM-DD`.
- **Time Formats**: Use `HH:MM:SS`.
- **RBAC**: If a user attempts an action not allowed for their role (e.g., a patient trying to generate slots), the API returns `403 Forbidden`.
