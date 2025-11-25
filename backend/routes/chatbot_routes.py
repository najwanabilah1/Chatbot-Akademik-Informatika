from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
import numpy as np
import pickle, os
from datetime import datetime
from sqlalchemy import func
from sklearn.metrics.pairwise import cosine_similarity

from backend.config import MODEL_DIR, db
from backend.db.models import ChatHistory, TopicStats

from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.sequence import pad_sequences

chat_bp = Blueprint("chat_bp", __name__)

# ===============================
# LOAD MAIN MODEL (LSTM)
# ===============================
MAIN_MODEL_PATH = os.path.join(MODEL_DIR, "main_model.h5")
TOKEN_MAIN = os.path.join(MODEL_DIR, "tokenizer_main.pkl")
LABEL_MAIN = os.path.join(MODEL_DIR, "label_main.pkl")

main_model = load_model(MAIN_MODEL_PATH) if os.path.exists(MAIN_MODEL_PATH) else None
tokenizer_main = pickle.load(open(TOKEN_MAIN, "rb")) if os.path.exists(TOKEN_MAIN) else None
le_main = pickle.load(open(LABEL_MAIN, "rb")) if os.path.exists(LABEL_MAIN) else None

# ===============================
# LOAD SEMANTIC FALLBACK (TF-IDF)
# ===============================
VEC_PATH = os.path.join(MODEL_DIR, "fallback_vectorizer.pkl")
MAT_PATH = os.path.join(MODEL_DIR, "fallback_matrix.pkl")
TEXT_PATH = os.path.join(MODEL_DIR, "fallback_texts.pkl")

vectorizer = pickle.load(open(VEC_PATH, "rb")) if os.path.exists(VEC_PATH) else None
matrix = pickle.load(open(MAT_PATH, "rb")) if os.path.exists(MAT_PATH) else None
fallback_texts = pickle.load(open(TEXT_PATH, "rb")) if os.path.exists(TEXT_PATH) else None

THRESHOLD = 0.3  # 🔹 Diturunkan dari 0.6 agar LSTM lebih sering digunakan


# ======================================================
# CHAT ENDPOINT
# ======================================================
@chat_bp.route("/chat", methods=["POST"])
@cross_origin()
def chat():
    data = request.json
    question = data.get("pertanyaan", "").strip().lower()  # 🔹 Normalisasi input
    npm = data.get("npm", None)

    if not question:
        return jsonify({"error": "Pertanyaan tidak boleh kosong"}), 400

    answer, source, confidence = "", "", 0.0

    # =====================================
    # 1) UTAMA → LSTM MODEL
    # =====================================
    if main_model and tokenizer_main and le_main:
        seq = tokenizer_main.texts_to_sequences([question])
        pad = pad_sequences(seq, maxlen=main_model.input_shape[1], padding="post")
        pred = main_model.predict(pad, verbose=0)

        confidence = float(np.max(pred))

        if confidence >= THRESHOLD:
            label_id = int(np.argmax(pred))
            answer = le_main.inverse_transform([label_id])[0]
            source = "dataset"
        else:
            # =====================================
            # 2) FALLBACK → SEMANTIC SEARCH (TF-IDF)
            # =====================================
            if vectorizer and matrix is not None and fallback_texts:
                q_vec = vectorizer.transform([question])
                sims = cosine_similarity(q_vec, matrix)
                idx = int(np.argmax(sims))
                confidence = float(np.max(sims))

                answer = fallback_texts[idx]
                source = "peraturan"
            else:
                answer = "⚠️ Model fallback (peraturan) belum tersedia."
                source = "none"

    else:
        answer = "⚠️ Model utama belum tersedia."
        source = "none"

    # =====================================
    # SIMPAN KE DATABASE
    # =====================================
    try:
        new_chat = ChatHistory(
            npm=npm,
            question=question,
            answer=answer,
            source=source,
            confidence=confidence
        )
        db.session.add(new_chat)

        # TOPIC SAVING
        topic_name = question[:100]
        exist = TopicStats.query.filter(
            func.lower(TopicStats.topic_name) == func.lower(topic_name)
        ).first()

        if exist:
            exist.mention_count += 1
            exist.last_updated = datetime.utcnow()
        else:
            new_topic = TopicStats(
                topic_name=topic_name,
                mention_count=1,
                last_updated=datetime.utcnow()
            )
            db.session.add(new_topic)

        db.session.commit()
    except Exception as e:
        print("❌ Error simpan chat:", e)
        db.session.rollback()

    # =====================================
    # RESPONSE
    # =====================================
    return jsonify({
        "jawaban": answer,
        "sumber": source,
        "confidence": confidence
    })
