# Graduation Project - Backend System Documentation

This document provides a comprehensive guide to the backend architecture, its operational flows, and an exhaustive reference for every API endpoint.

---

## 1. System Setup & Testing Tools

To facilitate a clean setup and automated testing, the following utility scripts are provided:

### A. Database Seeding (`seed_db.py`)
- **Purpose**: Initializes a fresh database with essential constants.
- **Action**: Creates default roles (`admin`, `clinic`, `doctor`, `user`) and standard medical specializations (e.g., Cardiology, Pediatrics).
- **Run**: `python seed_db.py`

### B. Admin Promotion (`promote_admin.py`)
- **Purpose**: Grants administrative privileges to any registered user.
- **Run**: `python promote_admin.py <email>`

### C. Exhaustive Automation Test (`test_automation_full.py`)
- **Purpose**: Simulates a high-load production environment.
- **Flow**: 
    1.  Seeds the database.
    2.  Promotes a system admin.
    3.  Registers a Clinic and two Doctors (one Clinic-Linked, one Independent).
    4.  Runs parallel booking journeys for both doctors.
    5.  Tests AI Diagnostics (Diabetes & X-Ray) and verifies Medical Records.
- **Run**: `python test_automation_full.py`

---

## 2. Core Functional Flows

### I. Identity & Recruitment
The system supports two doctor engagement models:
1.  **Clinic-Linked**: Doctors are invited by clinics via `POST /clinics/{id}/invitations`. Once accepted, the clinic manages their slots and bookings.
2.  **Independent**: Doctors manage their own profile and availability directly.

### II. Availability & Slot Generation
Scheduling is a two-step process:
1.  **Availability Rules**: Recurring weekly schedule (e.g., "Mondays 9 AM - 5 PM").
    - `day_of_week`: 0 (Monday) to 6 (Sunday).
2.  **Slot Generation**: Actual instances of time for a specific date range.
    - `POST /appointment-slots/generate` returns a list of created slot objects.

### III. Booking Lifecycle
- **Statuses**: `pending` → `confirmed` → `completed` / `cancelled`.
- **Verification**: Patients can rate only `completed` bookings.

---

## 3. API Reference (All Modules)

### /users - Authentication & Profiles
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| POST | `/users/register/user` | Patient registration with medical profile. |
| POST | `/users/register/clinic` | Clinic registration with facility details. |
| POST | `/users/register/doctor` | Doctor registration with professional info. |
| POST | `/users/login` | Authenticate and receive JWT. |
| GET | `/users/me` | Retrieve full profile of current user. |
| PATCH | `/users/me` | Update current user data. |
| GET | `/users/{uuid}` | Admin view of any user. |

### /clinics - Facility Management
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| GET | `/clinics/` | Public list of all clinics. |
| GET | `/clinics/{id}` | Detailed clinic profile. |
| GET | `/clinics/search/doctors` | Find doctors by specialty or location. |
| GET | `/clinics/{id}/doctors` | List doctors linked to a specific clinic. |
| POST | `/clinics/{id}/invitations` | Invite a doctor to join the clinic. |

### /doctors - Professional Management
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| GET | `/doctors/` | Public list of all active doctors. |
| GET | `/doctors/{id}` | Detailed doctor profile (bio, ratings). |
| GET | `/doctors/me/invitations` | View pending recruitment requests. |
| PATCH | `/doctors/me/invitations/{id}/respond` | Accept/Reject clinic invites. |

### /appointment-slots - Scheduling
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| POST | `/appointment-slots/generate` | Bulk generate slots from availability rules. |
| GET | `/appointment-slots/` | Filter available slots by doctor, clinic, or date. |
| PATCH | `/appointment-slots/{id}` | Update slot status or notes. |
| DELETE | `/appointment-slots/{id}` | Remove a specific slot. |

### /bookings - Appointment Lifecycle
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| POST | `/bookings/` | Patient books an available slot. |
| PATCH | `/bookings/{id}/confirm` | Authorized entity confirms the visit. |
| PATCH | `/bookings/{id}/complete` | Mark visit as finished. |
| PATCH | `/bookings/{id}/rate` | Patient provides 1-5 star feedback. |
| POST | `/bookings/{id}/notes` | Add clinical notes to the appointment. |

### /records - Health Data
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| GET | `/records/me` | Patient views their full medical history. |
| GET | `/records/user/{id}` | Doctor views patient history (authorized). |

### /analysis & /xray - AI Intelligence
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| POST | `/analysis/run` | Predict diabetes risk from vital signs. |
| POST | `/xray/upload` | Automate Chest X-Ray diagnosis (Normal/Pneumonia). |

### /chat - LLM Assistant
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| POST | `/chat/sessions` | Initialize AI consultation session. |
| POST | `/chat/sessions/{id}/messages` | Interactive chat exchange. |

### /audit & /roles - Administration
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| GET | `/audit/` | Full system activity log. |
| POST | `/roles/assign` | Assign RBAC roles (Admin/Doctor/Clinic). |
| POST | `/specializations/` | Add new medical fields. |

---

## 4. Security
- **Authentication**: JWT Bearer Tokens in `Authorization` header.
- **RBAC**: Access is strictly enforced per endpoint based on the `RoleEnum` (`admin`, `doctor`, `clinic`, `user`).
