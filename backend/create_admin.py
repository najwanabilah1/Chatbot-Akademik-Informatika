from backend.config import db, app
from backend.db.models import User
from werkzeug.security import generate_password_hash

def create_admin():
    """Tambahkan akun admin secara manual ke database"""
    with app.app_context():
        username = input("Masukkan username admin: ").strip()
        password = input("Masukkan password admin: ").strip()

        if not username or not password:
            print("❌ Username dan password wajib diisi!")
            return

        # Periksa apakah sudah ada admin dengan nama itu
        existing_admin = User.query.filter_by(name=username, role="admin").first()
        if existing_admin:
            print(f"⚠️ Admin dengan username '{username}' sudah ada.")
            return

        # Buat akun admin baru
        admin = User(
            npm=f"admin_{username}",
            name=username,
            password=generate_password_hash(password),
            role="admin"
        )
        db.session.add(admin)
        db.session.commit()
        print(f"✅ Admin '{username}' berhasil ditambahkan ke database!")

if __name__ == "__main__":
    create_admin()
