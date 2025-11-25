from backend.config import db
from datetime import datetime

# ======================
# TABEL USER
# ======================
class User(db.Model):
    __tablename__ = "users"  
    npm = db.Column(db.String(20), primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default="user")
    photo = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# ======================
# TABEL LOGIN HISTORY
# ======================
class LoginHistory(db.Model):
    __tablename__ = "login_history"
    id = db.Column(db.Integer, primary_key=True)
    npm = db.Column(db.String(20), db.ForeignKey('users.npm'), nullable=False)  # <- disesuaikan
    login_time = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship("User", backref="login_records", lazy=True)

# ======================
# TABEL CHAT SESSION
# ======================
class ChatSession(db.Model):
    __tablename__ = "chat_sessions"
    id = db.Column(db.Integer, primary_key=True)
    npm = db.Column(db.String(20), db.ForeignKey("users.npm"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    messages = db.relationship("ChatMessage", backref="session", lazy=True, cascade="all, delete-orphan")


# ======================
# TABEL CHAT MESSAGE
# ======================
class ChatMessage(db.Model):
    __tablename__ = "chat_messages"
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey("chat_sessions.id"), nullable=False)
    sender = db.Column(db.String(10))  # "user" atau "bot"
    message = db.Column(db.Text, nullable=False)  # ganti text -> message biar sama dengan route
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


# ======================
# TABEL CHAT HISTORY 
# ======================
class ChatHistory(db.Model):
    __tablename__ = "chat_history"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    npm = db.Column(db.String(20), db.ForeignKey("users.npm"), nullable=True)
    question = db.Column(db.Text, nullable=False)
    answer = db.Column(db.Text, nullable=False)
    source = db.Column(db.String(50))
    confidence = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow) 


# ======================
# TABEL STATISTIK TOPIK
# ======================
class TopicStats(db.Model):
    __tablename__ = "topic_stats"
    id = db.Column(db.Integer, primary_key=True)
    topic_name = db.Column(db.String(255), nullable=False)
    mention_count = db.Column(db.Integer, default=1)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)

# ======================
# TABEL DATASET & PERATURAN
# ======================
class Dataset(db.Model):
    __tablename__ = "dataset"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    pertanyaan = db.Column(db.Text, nullable=False)
    jawaban = db.Column(db.Text, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)


class Peraturan(db.Model):
    __tablename__ = "peraturan"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    sentence_number = db.Column(db.Integer, nullable=True)
    sentence = db.Column(db.Text, nullable=False)  
    filename = db.Column(db.String(255), nullable=True)  
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)