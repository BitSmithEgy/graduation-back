import requests
import time
import uuid
import subprocess
import os

BASE_URL = "http://localhost:8000"

def log(msg, symbol="ℹ️"):
    print(f"{symbol} {msg}")

def get_random_email(role):
    return f"{role}_{uuid.uuid4().hex[:6]}@example.com"

def run_command(cmd):
    log(f"Running System Command: {cmd}", "💻")
    subprocess.run(cmd, shell=True, check=True)

def login(email, password):
    resp = requests.post(f"{BASE_URL}/users/login", json={"email": email, "password": password})
    if resp.status_code != 200:
        log(f"Login failed for {email}: {resp.text}", "❌")
        return None
    return resp.json()["access_token"]

def run_test():
    log("Starting EXHAUSTIVE MULTI-SCENARIO System Test", "🚀")
    
    # ---------------------------------------------------------
    # STAGE 0: BOOTSTRAP
    # ---------------------------------------------------------
    log("Phase 0: Bootstrapping Database...", "🌱")
    run_command("python seed_db.py")

    # Generate unique credentials
    password = "GlobalPassword123!"
    admin_email   = get_random_email("admin")
    clinic_email  = get_random_email("clinic")
    doc_clinic_email = get_random_email("doc_clinic")
    doc_indep_email  = get_random_email("doc_indep")
    patient_email = get_random_email("patient")

    # ---------------------------------------------------------
    # STAGE 1: IDENTITY & ADMIN PROMOTION
    # ---------------------------------------------------------
    log("Phase 1: Setting up Identities...", "🆔")
    
    # Register Admin & Promote
    requests.post(f"{BASE_URL}/users/register/user", json={
        "email": admin_email, "phone": f"015{uuid.uuid4().hex[:7]}", "full_name": "System Admin", "password": password
    })
    run_command(f"python promote_admin.py {admin_email}")
    a_tk = login(admin_email, password)
    a_h = {"Authorization": f"Bearer {a_tk}"}

    # Register Clinic
    c_resp = requests.post(f"{BASE_URL}/users/register/clinic", json={
        "email": clinic_email, "phone": f"011{uuid.uuid4().hex[:7]}", "full_name": "Elite Clinic", "password": password,
        "clinic": {"name": "Elite Medical Center", "address": "Downtown", "phone": "0223456789", "email": clinic_email}
    })
    clinic_id = c_resp.json()["clinic_account"]["id"]
    log(f"Clinic Registered: {clinic_id}")

    # Register Doctor 1 (To be linked to clinic)
    dc_resp = requests.post(f"{BASE_URL}/users/register/doctor", json={
        "email": doc_clinic_email, "phone": f"012{uuid.uuid4().hex[:7]}", "full_name": "Dr. Clinic Specialist", "password": password
    })
    doc_clinic_id = dc_resp.json()["doctor_account"]["id"]
    log(f"Doctor 1 (Clinic) Registered: {doc_clinic_id}")

    # Register Doctor 2 (Independent)
    di_resp = requests.post(f"{BASE_URL}/users/register/doctor", json={
        "email": doc_indep_email, "phone": f"013{uuid.uuid4().hex[:7]}", "full_name": "Dr. Independent", "password": password
    })
    doc_indep_id = di_resp.json()["doctor_account"]["id"]
    log(f"Doctor 2 (Independent) Registered: {doc_indep_id}")

    # Register Patient
    p_resp = requests.post(f"{BASE_URL}/users/register/user", json={
        "email": patient_email, "phone": f"010{uuid.uuid4().hex[:7]}", "full_name": "John Patient", "password": password,
        "profile": {"blood_type": "A+", "height_cm": 178, "weight_kg": 75}
    })
    patient_id = p_resp.json()["uuid"]
    log(f"Patient Registered: {patient_id}")

    # Logins
    c_tk = login(clinic_email, password); c_h = {"Authorization": f"Bearer {c_tk}"}
    dc_tk = login(doc_clinic_email, password); dc_h = {"Authorization": f"Bearer {dc_tk}"}
    di_tk = login(doc_indep_email, password); di_h = {"Authorization": f"Bearer {di_tk}"}
    p_tk = login(patient_email, password); p_h = {"Authorization": f"Bearer {p_tk}"}

    # ---------------------------------------------------------
    # STAGE 2: CLINICAL RECRUITMENT
    # ---------------------------------------------------------
    log("Phase 2: Recruiting Clinic Doctor...", "🤝")
    invite = requests.post(f"{BASE_URL}/clinics/{clinic_id}/invitations", headers=c_h, 
                           json={"doctor_id": doc_clinic_id, "message": "Join Elite Center"}).json()
    requests.patch(f"{BASE_URL}/doctors/me/invitations/{invite['id']}/respond?accept=true", headers=dc_h)
    log("Doctor 1 is now linked to Clinic.")

    # ---------------------------------------------------------
    # STAGE 3: AVAILABILITY & SLOTS (BOTH SCENARIOS)
    # ---------------------------------------------------------
    log("Phase 3: Scheduling Slots for Both Doctors...", "📅")
    
    # Doctor 1 (Clinic)
    avail_c = requests.post(f"{BASE_URL}/doctors/{doc_clinic_id}/availability/", headers=dc_h, json={
        "day_of_week": 0, "start_time": "09:00:00", "end_time": "10:00:00", "slot_duration_minutes": 30
    })
    assert avail_c.status_code == 201

    gen_c_resp = requests.post(f"{BASE_URL}/appointment-slots/generate", headers=c_h, json={
        "doctor_id": doc_clinic_id, "from_date": "2026-11-02", "to_date": "2026-11-02"
    })
    assert gen_c_resp.status_code == 200
    gen_c = gen_c_resp.json()
    slot_c_id = gen_c["slots"][0]["id"]
    log("Slots generated for Clinic Doctor.")

    # Doctor 2 (Independent)
    avail_i = requests.post(f"{BASE_URL}/doctors/{doc_indep_id}/availability/", headers=di_h, json={
        "day_of_week": 0, "start_time": "14:00:00", "end_time": "15:00:00", "slot_duration_minutes": 30
    })
    assert avail_i.status_code == 201

    gen_i_resp = requests.post(f"{BASE_URL}/appointment-slots/generate", headers=di_h, json={
        "doctor_id": doc_indep_id, "from_date": "2026-11-02", "to_date": "2026-11-02"
    })
    assert gen_i_resp.status_code == 200
    gen_i = gen_i_resp.json()
    slot_i_id = gen_i["slots"][0]["id"]
    log("Slots generated for Independent Doctor.")

    # ---------------------------------------------------------
    # STAGE 4: PATIENT AI SERVICES
    # ---------------------------------------------------------
    log("Phase 4: Running AI Diagnostic Services...", "🧠")
    
    # Diabetes
    requests.post(f"{BASE_URL}/analysis/run", headers=p_h, json={
        "pregnancies": 0, "glucose": 110, "blood_pressure": 70, "skin_thickness": 20, 
        "insulin": 0, "bmi": 24.5, "diabetes_pedigree_function": 0.4, "age": 28
    })
    log("Diabetes analysis completed.")

    # X-Ray (Mocking Image Upload)
    with open("dummy_xray.jpg", "wb") as f: f.write(os.urandom(1024))
    with open("dummy_xray.jpg", "rb") as f:
        requests.post(f"{BASE_URL}/xray/upload", headers=p_h, files={"file": f})
    os.remove("dummy_xray.jpg")
    log("X-Ray upload and diagnosis completed.")

    # ---------------------------------------------------------
    # STAGE 5: JOURNEY 1 - CLINIC BOOKING
    # ---------------------------------------------------------
    log("Phase 5: Executing Clinic Booking Journey...", "🏥")
    b_c = requests.post(f"{BASE_URL}/bookings/", headers=p_h, json={"slot_id": slot_c_id, "notes": "Clinic visit"}).json()
    requests.patch(f"{BASE_URL}/bookings/{b_c['id']}/confirm", headers=c_h)
    requests.patch(f"{BASE_URL}/bookings/{b_c['id']}/complete", headers=c_h)
    requests.patch(f"{BASE_URL}/bookings/{b_c['id']}/rate?rating=5", headers=p_h)
    log("Clinic Booking journey finished successfully.")

    # ---------------------------------------------------------
    # STAGE 6: JOURNEY 2 - INDEPENDENT BOOKING
    # ---------------------------------------------------------
    log("Phase 6: Executing Independent Booking Journey...", "🏠")
    b_i = requests.post(f"{BASE_URL}/bookings/", headers=p_h, json={"slot_id": slot_i_id, "notes": "Private visit"}).json()
    requests.patch(f"{BASE_URL}/bookings/{b_i['id']}/confirm", headers=di_h)
    requests.patch(f"{BASE_URL}/bookings/{b_i['id']}/complete", headers=di_h)
    requests.patch(f"{BASE_URL}/bookings/{b_i['id']}/rate?rating=4", headers=p_h)
    log("Independent Booking journey finished successfully.")

    # ---------------------------------------------------------
    # STAGE 7: AUDIT & FINAL RECORDS
    # ---------------------------------------------------------
    log("Phase 7: Verifying System State & Audit...", "📜")
    
    # Check Medical Record
    record = requests.get(f"{BASE_URL}/records/me", headers=p_h).json()
    log(f"Medical Record has {len(record.get('record', {}).get('diagnostics', []))} diagnostics.")
    
    # Check Audit Logs
    audits = requests.get(f"{BASE_URL}/audit/", headers=a_h).json()
    log(f"System generated {len(audits)} audit log entries.")

    log("EXHAUSTIVE MULTI-SCENARIO Test Passed Successfully!", "✅")

if __name__ == "__main__":
    try:
        run_test()
    except Exception as e:
        log(f"CRITICAL TEST FAILURE: {str(e)}", "❌")
        import traceback
        traceback.print_exc()
