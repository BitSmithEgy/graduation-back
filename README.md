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
