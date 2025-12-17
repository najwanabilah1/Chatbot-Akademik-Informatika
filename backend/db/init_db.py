from backend.config import db, app
from backend.db.models import User, ChatHistory, Dataset, Peraturan, WebsiteStats

with app.app_context():
    db.create_all()
    print("✅ Database & tabel berhasil dibuat!")
