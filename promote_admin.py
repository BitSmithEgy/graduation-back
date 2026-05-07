import sys
from sqlalchemy.orm import Session
from database import SessionLocal
from models import User, Role, UserRole

def promote(email):
    db = SessionLocal()
    user = db.query(User).filter(User.email == email).first()
    if not user:
        print(f"❌ User with email {email} not found")
        return
    
    admin_role = db.query(Role).filter(Role.role_name_en == "admin").first()
    if not admin_role:
        print("❌ Admin role not found. Run seed_db.py first.")
        return
    
    # Check if already admin
    exists = db.query(UserRole).filter(UserRole.user_id == user.uuid, UserRole.role_id == admin_role.role_id).first()
    if exists:
        print(f"✅ User {email} is already an admin")
        return
    
    db.add(UserRole(user_id=user.uuid, role_id=admin_role.role_id))
    db.commit()
    print(f"🚀 User {email} promoted to ADMIN successfully")
    db.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python promote_admin.py <email>")
    else:
        promote(sys.argv[1])
