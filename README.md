# API Endpoints Summary

Base prefix: `/users`

---

## Authentication

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `POST` | `/users/register/user` | Public | Register a normal user account |
| `POST` | `/users/register/clinic` | Public | Register a clinic account |
| `POST` | `/users/login` | Public | Login and receive JWT token (cookie + body) |
| `POST` | `/users/logout` | Public | Clear auth cookie |

### `POST /users/register/user`
```json
{
  "email": "john@example.com",
  "phone": "+201012345678",
  "full_name": "John Doe",
  "password": "secret123",
  "language_preference": "en",
  "profile": {
    "date_of_birth": "1995-06-15",
    "gender": "male",
    "blood_type": "O+",
    "height": "180",
    "weight": "75",
    "known_allergies": "Penicillin",
    "chronic_conditions": "None",
    "emergency_contact_name": "Jane Doe",
    "emergency_contact_phone": "+201098765432"
  }
}
```

### `POST /users/register/clinic`
```json
{
  "email": "clinic@example.com",
  "phone": "+201012345678",
  "full_name": "Dr. Ahmed Ali",
  "password": "secret123",
  "language_preference": "ar",
  "clinic": {
    "name": "Al Shifa Clinic",
    "address": "123 Tahrir St, Cairo",
    "phone": "+20224567890",
    "email": "info@alshifa.com",
    "location": "30.0444,31.2357"
  }
}
```

### `POST /users/login`
```json
{
  "email": "john@example.com",
  "password": "secret123"
}
```
**Response:**
```json
{
  "access_token": "<jwt>",
  "token_type": "bearer",
  "user": { }
}
```

---

## Current User `/me`

> All `/me` routes require a valid JWT (cookie or `Authorization: Bearer <token>`).

| Method | Endpoint | Role | Description |
|--------|----------|------|-------------|
| `GET` | `/users/me` | Any | Get current user info |
| `PUT` | `/users/me` | Any | Update shared user fields |
| `DELETE` | `/users/me` | Any | Soft-delete own account |
| `GET` | `/users/me/profile` | `user` only | Get user medical profile |
| `POST` | `/users/me/profile` | `user` only | Create user medical profile |
| `PATCH` | `/users/me/profile` | `user` only | Partially update user medical profile |
| `GET` | `/users/me/clinic` | `clinic` only | Get clinic details |
| `PATCH` | `/users/me/clinic` | `clinic` only | Partially update clinic details |

### `PUT /users/me` — Update shared fields
```json
{
  "phone": "+201099999999",
  "full_name": "John Updated",
  "password": "newpassword123",
  "language_preference": "ar"
}
```

### `POST /users/me/profile` — Create profile *(role = user)*
```json
{
  "date_of_birth": "1995-06-15",
  "gender": "male",
  "blood_type": "A+",
  "height": "175",
  "weight": "70",
  "known_allergies": "None",
  "chronic_conditions": "Diabetes",
  "emergency_contact_name": "Sara Doe",
  "emergency_contact_phone": "+201011112222"
}
```

### `PATCH /users/me/profile` — Partial update *(role = user)*
```json
{
  "weight": "72",
  "known_allergies": "Penicillin, Aspirin"
}
```

### `PATCH /users/me/clinic` — Partial update *(role = clinic)*
```json
{
  "address": "456 Ramses Ave, Cairo",
  "phone": "+20221234567"
}
```

---

## Admin Endpoints

> All admin routes require `role = admin`.

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/users/` | List all non-deleted users |
| `GET` | `/users/{user_id}` | Get a specific user by UUID |
| `PATCH` | `/users/{user_id}/role` | Change a user's role |
| `PATCH` | `/users/{user_id}/switch` | Toggle `is_active` on/off |
| `DELETE` | `/users/{user_id}` | Soft-delete a user |

### `PATCH /users/{user_id}/role`
```
PATCH /users/abc-123-uuid/role?role=clinic
```
Accepted values: `user` · `clinic` · `admin`

### `PATCH /users/{user_id}/switch`
```
PATCH /users/abc-123-uuid/switch
```
Toggles `is_active` — no body required.

### `DELETE /users/{user_id}`
Sets `deleted_at` timestamp. User is excluded from all listings but data is preserved.

---

## Analysis Endpoint
### `POST /analysis/run`
```json
{
  "pregnancies": 6,
  "glucose": 148.0,
  "blood_pressure": 72.0,
  "skin_thickness": 35.0,
  "insulin": 125.0,
  "bmi": 33.6,
  "diabetes_pedigree_function": 0.627,
  "age": 50
}
```

## X-Ray Endpoint
### `POST /xray/upload`

**Request:** `multipart/form-data`

| Field | Type   | Required | Description        |
|-------|--------|----------|--------------------|
| file  | binary | ✅       | X-ray image file   |

**Accepted formats:** `.jpg`, `.jpeg`, `.png`

## Role-Based Access Summary

| Feature | `user` | `clinic` | `admin` |
|---------|--------|----------|---------|
| Register | ✅ | ✅ | — |
| Login / Logout | ✅ | ✅ | ✅ |
| View own account `/me` | ✅ | ✅ | ✅ |
| Update own account | ✅ | ✅ | ✅ |
| Delete own account | ✅ | ✅ | ✅ |
| Medical profile `/me/profile` | ✅ | ❌ | ❌ |
| Clinic details `/me/clinic` | ❌ | ✅ | ❌ |
| List all users | ❌ | ❌ | ✅ |
| Manage any user | ❌ | ❌ | ✅ |

---

## Response Shapes

### `UserWithProfileOut` *(role = user)*
```json
{
  "uuid": "abc-123",
  "email": "john@example.com",
  "phone": "+201012345678",
  "full_name": "John Doe",
  "language_preference": "en",
  "role": "user",
  "is_active": true,
  "created_at": "2024-01-01T00:00:00",
  "updated_at": "2024-01-02T00:00:00",
  "profile": {
    "id": "prof-456",
    "user_id": "abc-123",
    "date_of_birth": "1995-06-15",
    "gender": "male",
    "blood_type": "O+",
    "height": "180",
    "weight": "75",
    "known_allergies": "Penicillin",
    "chronic_conditions": "None",
    "emergency_contact_name": "Jane Doe",
    "emergency_contact_phone": "+201098765432",
    "created_at": "2024-01-01T00:00:00",
    "updated_at": null
  }
}
```

### `UserWithClinicOut` *(role = clinic)*
```json
{
  "uuid": "xyz-789",
  "email": "clinic@example.com",
  "phone": "+201012345678",
  "full_name": "Dr. Ahmed Ali",
  "language_preference": "ar",
  "role": "clinic",
  "is_active": true,
  "created_at": "2024-01-01T00:00:00",
  "updated_at": null,
  "clinic": {
    "id": "cln-321",
    "user_id": "xyz-789",
    "name": "Al Shifa Clinic",
    "address": "123 Tahrir St, Cairo",
    "phone": "+20224567890",
    "email": "info@alshifa.com",
    "location": "30.0444,31.2357",
    "created_at": "2024-01-01T00:00:00",
    "updated_at": null
  }
}
```

---

## Error Codes

| Status | Meaning |
|--------|---------|
| `400` | Email or phone already registered / Profile already exists |
| `401` | Invalid credentials |
| `403` | Account deactivated / deleted / wrong role for endpoint |
| `404` | User / profile / clinic not found |

---

## Doctors Management

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `GET` | `/doctors/` | Public | List all active doctors |
| `GET` | `/doctors/{id}` | Public | Get specific doctor details |
| `POST` | `/doctors/` | `clinic` | Add a new doctor to your clinic |
| `PUT` | `/doctors/{id}` | `clinic`/`admin` | Update doctor information |
| `DELETE` | `/doctors/{id}` | `clinic`/`admin` | Soft delete a doctor |

### `POST /doctors/`
```json
{
  "full_name": "Dr. Sarah Smith",
  "specialization_id": "uuid-specialization",
  "language_spoken": "English, Arabic",
  "bio_en": "Expert in Cardiology...",
  "bio_ar": "خبير في أمراض القلب...",
  "consultation_price_egp": 500,
  "years_of_experiance": 10,
  "license_number": "LIC123456",
  "is_active": true
}
```

---

## Availability & Slots

Managing a doctor's schedule involves two steps: defining **Availability Rules** and generating **Appointment Slots**.

### 1. Availability Rules
Define the recurring weekly schedule for a doctor.

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `GET` | `/doctors/{id}/availability/` | Public | List doctor's availability rules |
| `POST` | `/doctors/{id}/availability/` | `clinic`/`admin` | Create a recurring schedule rule |

**Example Rule:** Mondays from 09:00 to 17:00 with 30-minute slots.
```json
{
  "day_of_week": 0,
  "start_time": "09:00:00",
  "end_time": "17:00:00",
  "slot_duration_minutes": 30
}
```

### 2. Appointment Slots
Slots are the actual bookable time units. They can be generated in bulk based on availability rules.

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `GET` | `/appointment-slots/` | Public | List available slots (filter by `doctor_id`) |
| `POST` | `/appointment-slots/generate` | `clinic`/`admin` | Bulk generate slots for a date range |

**Generate Slots Request:**
```json
{
  "doctor_id": "uuid-doctor",
  "from_date": "2024-05-20",
  "to_date": "2024-05-27"
}
```

---

## Booking Flow

The booking process follows a state-machine logic to ensure data integrity.

### Step 1: Find a Slot
The patient searches for available slots for a specific doctor.
`GET /appointment-slots/?doctor_id={id}&slot_status=available`

### Step 2: Create Booking
The patient selects a `slot_id` and creates a booking. The slot status automatically changes to `booked`.
`POST /bookings/`
```json
{
  "slot_id": "uuid-slot"
}
```
*Note: The booking starts in `pending` status.*

### Step 3: Confirmation (Clinic)
The clinic reviews and confirms the booking.
`PATCH /bookings/{id}/confirm`

### Step 4: Completion or Cancellation
After the visit, the clinic marks it as complete. Alternatively, either party can cancel.
- **Complete:** `PATCH /bookings/{id}/complete`
- **Cancel:** `PATCH /bookings/{id}/cancel` (Releases the slot back to `available`)

### Step 5: Post-Booking Actions
- **Rate Doctor:** `PATCH /bookings/{id}/rate?rating=5` (Only for `completed` bookings)
- **Get Invoice:** `GET /bookings/{id}/invoice`

### Booking Status Summary
`pending` ➔ `confirmed` ➔ `completed` | `cancelled`

