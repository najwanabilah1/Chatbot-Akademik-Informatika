from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
from backend.config import db, UPLOADS_DIR
from backend.db.models import (
    User, ChatHistory, TopicStats,
    LoginHistory, ChatSession, ChatMessage,
    Dataset, Peraturan
)
from sqlalchemy import func, desc
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from backend.utils.load_data import load_dataset_to_db, load_peraturan_to_db
import traceback
from backend.utils.pdf_parser import save_pdf_to_txt, save_word_to_txt
from backend.utils.retrain_model import retrain_main_from_db, retrain_all
import os

admin_bp = Blueprint("admin_bp", __name__, url_prefix="/api/admin")


# ================================
# 🔐 LOGIN ADMIN
# ================================
@admin_bp.route("/login", methods=["POST"])
def admin_login():
    data = request.json
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"error": "Kolom tidak boleh kosong"}), 400

    admin = User.query.filter_by(name=username, role="admin").first()
    if not admin or not check_password_hash(admin.password, password):
        return jsonify({"error": "Username atau Password salah"}), 401

    return jsonify({"message": "Login berhasil", "name": admin.name, "role": admin.role})


# ======================
# 📊 DASHBOARD
# ======================
@admin_bp.route("/dashboard_stats", methods=["GET"])
def dashboard_stats():
    try:
        today = datetime.utcnow().date()

        total_users = User.query.filter_by(role="user").count()

        total_questions_today = ChatMessage.query.filter(
            ChatMessage.sender == "user",
            func.date(ChatMessage.timestamp) == today
        ).count()

        total_logins_today = LoginHistory.query.filter(
            func.date(LoginHistory.login_time) == today
        ).count()

        avg_confidence = (
            db.session.query(func.avg(ChatHistory.confidence))
            .filter(func.date(ChatHistory.created_at) == today)
            .scalar() or 0
        )

        one_week_ago = today - timedelta(days=6)
        start_of_week = datetime.combine(one_week_ago, datetime.min.time())
        end_of_today = datetime.combine(today, datetime.max.time())

        # Grafik chat activity
        chat_activity = (
            db.session.query(
                func.date(ChatMessage.timestamp).label("tanggal"),
                func.count(ChatMessage.id).label("jumlah")
            )
            .filter(
                ChatMessage.sender == "user",
                ChatMessage.timestamp >= start_of_week,
                ChatMessage.timestamp <= end_of_today
            )
            .group_by(func.date(ChatMessage.timestamp))
            .order_by(func.date(ChatMessage.timestamp))
            .all()
        )

        chat_data = [
            {"tanggal": str(row.tanggal), "jumlah": row.jumlah}
            for row in chat_activity
        ]

        # Grafik login activity
        login_activity = (
            db.session.query(
                func.date(LoginHistory.login_time).label("tanggal"),
                func.count(LoginHistory.id).label("jumlah")
            )
            .filter(
                LoginHistory.login_time >= start_of_week,
                LoginHistory.login_time <= end_of_today
            )
            .group_by(func.date(LoginHistory.login_time))
            .order_by(func.date(LoginHistory.login_time))
            .all()
        )

        login_data = [
            {"tanggal": str(row.tanggal), "jumlah": row.jumlah}
            for row in login_activity
        ]

        # Top 5 topics
        top_topics = (
            TopicStats.query.order_by(desc(TopicStats.mention_count))
            .limit(5)
            .all()
        )

        top_topic_data = [
            {"topic": t.topic_name, "count": t.mention_count}
            for t in top_topics
        ]

        # Recent chat sessions
        recent_chats = (
            db.session.query(
                ChatSession.id.label("session_id"),
                User.name.label("user_name"),
                User.npm.label("npm"),
                User.role.label("status"),
                func.count(ChatMessage.id).label("total_messages"),
                func.max(ChatMessage.timestamp).label("last_chat")
            )
            .join(User, ChatSession.npm == User.npm)
            .join(ChatMessage, ChatMessage.session_id == ChatSession.id)
            .filter(ChatMessage.timestamp >= start_of_week)
            .group_by(ChatSession.id, User.name, User.npm, User.role)
            .order_by(desc(func.max(ChatMessage.timestamp)))
            .limit(10)
            .all()
        )

        recent_chat_data = [
            {
                "session_id": r.session_id,
                "npm": r.npm,
                "user_name": r.user_name,
                "status": r.status,
                "total_messages": r.total_messages,
                "last_chat": r.last_chat.strftime("%Y-%m-%d %H:%M:%S")
                if r.last_chat else None,
            }
            for r in recent_chats
        ]

        return jsonify({
            "cards": {
                "total_users": total_users,
                "questions_today": total_questions_today,
                "total_logins_today": total_logins_today,
                "avg_confidence": round(avg_confidence, 2),
            },
            "charts": {
                "chat_activity": chat_data,
                "login_activity": login_data,
                "top_topics": top_topic_data,
            },
            "recent_conversations": recent_chat_data,
        })

    except Exception as e:
        print("❌ Error di dashboard_stats:", e)
        return jsonify({"error": str(e)}), 500


# ================================
# 👥 MANAJEMEN USER
# ================================
@admin_bp.route("/users", methods=["GET", "POST"])
def users_list_add():
    if request.method == "GET":
        users = User.query.filter_by(role="user").all()
        return jsonify([
            {"npm": u.npm, "name": u.name, "role": u.role}
            for u in users
        ])

    if request.method == "POST":
        data = request.json
        npm = data.get("npm")
        name = data.get("name")
        role = data.get("role", "user")
        password = data.get("password") or "123456"

        if not npm or not name:
            return jsonify({"error": "NPM dan Name wajib diisi"}), 400

        if User.query.get(npm):
            return jsonify({"error": "User sudah ada"}), 400

        new_user = User(
            npm=npm,
            name=name,
            role=role,
            password=generate_password_hash(password)
        )
        db.session.add(new_user)
        db.session.commit()

        return jsonify({"message": f"User {name} berhasil ditambahkan"}), 201


@admin_bp.route("/users/<string:npm>", methods=["PUT", "DELETE"])
def user_update_delete(npm):
    user = User.query.get(npm)
    if not user:
        return jsonify({"error": "User tidak ditemukan"}), 404

    if request.method == "PUT":
        data = request.json
        user.name = data.get("name", user.name)
        user.role = data.get("role", user.role)

        if data.get("password"):
            user.password = generate_password_hash(data["password"])

        db.session.commit()
        return jsonify({"message": f"User {npm} berhasil diperbarui"})

    if request.method == "DELETE":
        LoginHistory.query.filter_by(npm=user.npm).delete()

        sessions = ChatSession.query.filter_by(npm=user.npm).all()
        for s in sessions:
            ChatMessage.query.filter_by(session_id=s.id).delete()
            ChatHistory.query.filter_by(npm=user.npm).delete()
            db.session.delete(s)

        TopicStats.query.filter_by(topic_name=user.name).delete()

        db.session.delete(user)
        db.session.commit()

        return jsonify({"message": f"User {npm} berhasil dihapus beserta seluruh riwayatnya"})


# ================================
# 📂 UPLOAD DATASET (CSV)
# ================================
@admin_bp.route("/upload_dataset", methods=["POST"])
def upload_dataset():
    if "file" not in request.files:
        return jsonify({"error": "Tidak ada file yang diunggah"}), 400

    file = request.files["file"]
    dataset_dir = os.path.join(UPLOADS_DIR, "datasets")
    os.makedirs(dataset_dir, exist_ok=True)

    save_path = os.path.join(dataset_dir, file.filename)
    file.save(save_path)

    try:
        inserted, skipped = load_dataset_to_db(save_path)
        msg = f"Dataset '{file.filename}' berhasil diunggah dan disimpan ke database"
        if skipped:
            msg += f" (note: {skipped} baris dilewati karena format tidak sesuai)"
        return jsonify({
            "message": msg,
            "inserted_rows": inserted,
            "skipped_rows": skipped
        })
    except Exception as e:
        # print full traceback to server log for debugging
        print("❌ Error di upload_dataset:")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


# ================================
# 📄 LIST & DELETE DATASET
# ================================
@admin_bp.route("/dataset", methods=["GET"])
def get_dataset():
    data = Dataset.query.order_by(Dataset.id.desc()).all()
    return jsonify([
        {
            "id": d.id,
            "pertanyaan": d.pertanyaan,
            "jawaban": d.jawaban,
            "updated_at": d.updated_at.strftime("%Y-%m-%d %H:%M:%S")
        }
        for d in data
    ])


@admin_bp.route("/dataset/<int:id>", methods=["DELETE"])
def delete_dataset(id):
    data = Dataset.query.get(id)
    if not data:
        return jsonify({"error": "Dataset tidak ditemukan"}), 404

    db.session.delete(data)
    db.session.commit()

    return jsonify({"message": f"Dataset ID {id} berhasil dihapus"})


# ================================
# 📘 UPLOAD PDF PERATURAN
# ================================
@admin_bp.route("/upload_pdf", methods=["POST"])
def upload_pdf():
    if "file" not in request.files:
        return jsonify({"error": "Tidak ada file yang diunggah"}), 400

    file = request.files["file"]
    pdf_dir = os.path.join(UPLOADS_DIR, "pdfs")
    os.makedirs(pdf_dir, exist_ok=True)

    pdf_path = os.path.join(pdf_dir, file.filename)
    file.save(pdf_path)

    try:
        save_pdf_to_txt(pdf_path)
        load_peraturan_to_db()
        return jsonify({"message": f"PDF '{file.filename}' berhasil diproses dan disimpan ke database"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ================================
# 📄 UPLOAD FILE WORD (DOCX/DOC)
# ================================
@admin_bp.route("/upload_word", methods=["POST"])
def upload_word():
    if "file" not in request.files:
        return jsonify({"error": "Tidak ada file yang diunggah"}), 400

    file = request.files["file"]
    
    # Validasi format file
    if not (file.filename.lower().endswith('.docx') or file.filename.lower().endswith('.doc')):
        return jsonify({"error": "Hanya file .docx atau .doc yang diizinkan"}), 400
    
    word_dir = os.path.join(UPLOADS_DIR, "words")
    os.makedirs(word_dir, exist_ok=True)

    word_path = os.path.join(word_dir, file.filename)
    file.save(word_path)

    try:
        save_word_to_txt(word_path)
        load_peraturan_to_db()
        return jsonify({"message": f"File Word '{file.filename}' berhasil diproses dan disimpan ke database"})
    except Exception as e:
        print("❌ Error di upload_word:")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


# ================================
# 📁 LIST UPLOADED FILES (datasets / pdfs)
# ================================
@admin_bp.route("/uploads/datasets", methods=["GET"])
def list_uploaded_datasets():
    try:
        dataset_dir = os.path.join(UPLOADS_DIR, "datasets")
        files = []
        if os.path.isdir(dataset_dir):
            for f in sorted(os.listdir(dataset_dir), key=lambda x: os.path.getmtime(os.path.join(dataset_dir, x)), reverse=True):
                if not f.lower().endswith('.csv'):
                    continue
                fp = os.path.join(dataset_dir, f)
                try:
                    stat = os.stat(fp)
                    files.append({
                        "filename": f,
                        "uploaded_at": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
                        "size": stat.st_size
                    })
                except Exception:
                    continue
        return jsonify(files)
    except Exception as e:
        print("❌ Error listing dataset uploads:", e)
        return jsonify({"error": str(e)}), 500


@admin_bp.route("/uploads/pdfs", methods=["GET"])
def list_uploaded_pdfs():
    try:
        pdf_dir = os.path.join(UPLOADS_DIR, "pdfs")
        files = []
        if os.path.isdir(pdf_dir):
            for f in sorted(os.listdir(pdf_dir), key=lambda x: os.path.getmtime(os.path.join(pdf_dir, x)), reverse=True):
                if not f.lower().endswith('.pdf'):
                    continue
                fp = os.path.join(pdf_dir, f)
                try:
                    stat = os.stat(fp)
                    files.append({
                        "filename": f,
                        "uploaded_at": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
                        "size": stat.st_size
                    })
                except Exception:
                    continue
        return jsonify(files)
    except Exception as e:
        print("❌ Error listing pdf uploads:", e)
        return jsonify({"error": str(e)}), 500

# ================================
# 🧠 RETRAIN MODEL LSTM + FALLBACK
# ================================
@admin_bp.route("/retrain", methods=["POST"])
def retrain():
    try:
        # retrain both main model and fallback
        retrain_all()
        return jsonify({"message": "Model berhasil dilatih ulang"})
    except Exception as e:
        print("❌ Error di retrain:")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
