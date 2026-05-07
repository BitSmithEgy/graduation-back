from sqlalchemy.orm import Session
from database import SessionLocal, engine, Base
from models import Role, Specialization

def seed():
    print("🌱 Seeding database...")
    db = SessionLocal()
    
    # 1. Create Roles
    roles = [
        {"role_name_en": "admin",  "role_name_ar": "مدير"},
        {"role_name_en": "clinic", "role_name_ar": "عيادة"},
        {"role_name_en": "doctor", "role_name_ar": "طبيب"},
        {"role_name_en": "user",   "role_name_ar": "مريض"}
    ]
    
    for r in roles:
        exists = db.query(Role).filter(Role.role_name_en == r["role_name_en"]).first()
        if not exists:
            db.add(Role(**r))
            print(f"Created role: {r['role_name_en']}")

    # 2. Create Specializations
    specs = [
        {"name_en": "Cardiology", "name_ar": "أمراض القلب"},
        {"name_en": "Dermatology", "name_ar": "الأمراض الجلدية"},
        {"name_en": "Pediatrics", "name_ar": "طب الأطفال"},
        {"name_en": "Neurology", "name_ar": "أمراض المخ والأعصاب"},
        {"name_en": "Orthopedics", "name_ar": "جراحة العظام"}
    ]
    
    for s in specs:
        exists = db.query(Specialization).filter(Specialization.name_en == s["name_en"]).first()
        if not exists:
            db.add(Specialization(**s))
            print(f"Created specialization: {s['name_en']}")

    db.commit()
    db.close()
    print("✅ Seeding complete.")

if __name__ == "__main__":
    seed()
