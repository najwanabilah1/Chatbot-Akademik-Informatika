import os
from datetime import datetime
from flask_cors import cross_origin
from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from backend.config import db, app
from backend.db.models import User, ChatSession, ChatMessage, LoginHistory

user_bp = Blueprint("user_bp", __name__)

# =========================
# KONFIGURASI UPLOAD FOTO
# =========================
UPLOAD_FOLDER = os.path.join(app.root_path, "static", "uploads", "profile")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# =========================
# REGISTER (SIGN UP)
# =========================
@user_bp.route("/register", methods=["POST"])
def register():
    name = request.form.get("name")
    npm = request.form.get("npm")
    password = request.form.get("password")
    photo = request.files.get("photo")

    if not npm or not name or not password:
        return jsonify({"error": "Semua field wajib diisi"}), 400

    if User.query.filter_by(npm=npm).first():
        return jsonify({"error": "NPM sudah terdaftar"}), 400

    photo_filename = None
    if photo:
        filename = secure_filename(photo.filename)
        photo_filename = f"{npm}_{filename}"
        photo.save(os.path.join(UPLOAD_FOLDER, photo_filename))

    hashed_pw = generate_password_hash(password)
    new_user = User(
        npm=npm,
        name=name,
        password=hashed_pw,
        role="user",
        photo=photo_filename
    )

    db.session.add(new_user)
    db.session.commit()
    return jsonify({"message": "Register success"}), 200

# =========================
# LOGIN
# =========================
@user_bp.route("/login", methods=["POST"])
def login():
    data = request.json
    npm = data.get("npm")
    pw = data.get("password")

    if not npm or not pw:
        return jsonify({"error": "Harap isi semua kolom"}), 400

    u = User.query.filter_by(npm=npm).first()
    if not u or not check_password_hash(u.password, pw):
        return jsonify({"error": "NPM atau Password salah"}), 401
    
    u.last_login = datetime.utcnow()
    login_record = LoginHistory(npm=u.npm, login_time=datetime.utcnow())
    db.session.add(login_record)
    db.session.commit()

    return jsonify({
        "message": "login success",
        "npm": u.npm,
        "name": u.name,
        "role": u.role
    })

# =========================
# PROFILE USER
# =========================
@user_bp.route("/profile/<string:npm>", methods=["GET", "PUT"])
def profile(npm):
    u = User.query.filter_by(npm=npm).first()
    if not u:
        return jsonify({"error": "User tidak ditemukan"}), 404

    if request.method == "GET":
        return jsonify({
            "npm": u.npm,
            "name": u.name,
            "photo": u.photo,
            "role": u.role
        })

    data = request.form or request.json or {}
    u.name = data.get("name", u.name)
    if data.get("password"):
        u.password = generate_password_hash(data["password"])

    if "photo" in request.files:
        photo = request.files["photo"]
        if photo.filename:
            filename = secure_filename(photo.filename)
            photo_filename = f"{u.npm}_{filename}"
            upload_path = os.path.join(UPLOAD_FOLDER, photo_filename)
            photo.save(upload_path)
            u.photo = photo_filename

    db.session.commit()
    return jsonify({"message": "Profile updated successfully"})

# =========================
# BUAT SESI CHAT BARU
# =========================
@user_bp.route("/chat/session", methods=["POST"])
def create_chat_session():
    data = request.json
    npm = data.get("npm")

    if not npm:
        return jsonify({"error": "NPM tidak boleh kosong"}), 400

    session = ChatSession(npm=npm)
    db.session.add(session)
    db.session.commit()

    return jsonify({
        "message": "Chat session created",
        "session_id": session.id,
        "created_at": session.created_at.isoformat()
    })

# =========================
# SIMPAN PESAN DALAM SESI
# =========================
@user_bp.route("/chat/message", methods=["POST"])
def add_chat_message():
    data = request.json
    session_id = data.get("session_id")
    sender = data.get("sender")
    message = data.get("message")

    if not all([session_id, sender, message]):
        return jsonify({"error": "Data tidak lengkap"}), 400

    chat_msg = ChatMessage(
        session_id=session_id,
        sender=sender,
        message=message
    )
    db.session.add(chat_msg)
    db.session.commit()

    return jsonify({"message": "Message saved"})

# =========================
# LIHAT SEMUA RIWAYAT CHAT
# =========================
@user_bp.route("/chat/history/<string:npm>", methods=["GET"])
def get_chat_history(npm):
    sessions = ChatSession.query.filter_by(npm=npm).order_by(ChatSession.created_at.desc()).all()
    result = []

    for s in sessions:
        messages = ChatMessage.query.filter_by(session_id=s.id).order_by(ChatMessage.timestamp.asc()).all()
        result.append({
            "session_id": s.id,
            "created_at": s.created_at.isoformat(),
            "messages": [
                {"sender": m.sender, "message": m.message, "timestamp": m.timestamp.isoformat()}
                for m in messages
            ]
        })

    return jsonify(result)

# =========================
# AMBIL DETAIL SATU SESI CHAT
# =========================
@user_bp.route("/chat/session/<int:session_id>", methods=["GET"])
def get_single_session(session_id):
    session = ChatSession.query.get(session_id)
    if not session:
        return jsonify({"error": "Sesi tidak ditemukan"}), 404

    messages = ChatMessage.query.filter_by(session_id=session_id).order_by(ChatMessage.timestamp.asc()).all()
    return jsonify({
        "session_id": session.id,
        "npm": session.npm,
        "created_at": session.created_at.isoformat(),
        "messages": [
            {"sender": m.sender, "content": m.message, "timestamp": m.timestamp.isoformat()}
            for m in messages
        ]
    })
