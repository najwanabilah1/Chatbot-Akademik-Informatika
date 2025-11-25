import os
import sys
import pickle
from sklearn.feature_extraction.text import TfidfVectorizer
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing.sequence import pad_sequences
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Embedding, LSTM, Dense, Dropout, Bidirectional
from sklearn.preprocessing import LabelEncoder

# ===== FIX IMPORT PATHS =====
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from backend.config import app
from backend.db.models import Dataset, Peraturan

# ===== MODEL FOLDER =====
MODEL_DIR = os.path.join(os.path.dirname(__file__), "../model")
os.makedirs(MODEL_DIR, exist_ok=True)

# ==============================================================  
# 🔹 TRAIN MAIN MODEL (Dataset Q&A)
# ==============================================================
def retrain_main_from_db(epochs=30):
    with app.app_context():
        data = Dataset.query.all()
        if not data:
            raise ValueError("❌ Tabel Dataset kosong.")
        questions = [d.pertanyaan for d in data]
        answers = [d.jawaban for d in data]

    # Tokenize input
    tokenizer = Tokenizer(oov_token="<OOV>")
    tokenizer.fit_on_texts(questions)
    X = tokenizer.texts_to_sequences(questions)
    X = pad_sequences(X, padding="post")

    # Encode labels
    le = LabelEncoder()
    y = le.fit_transform(answers)

    # Build improved LSTM model
    model = Sequential([
        Embedding(len(tokenizer.word_index) + 1, 128, input_length=X.shape[1]),
        Bidirectional(LSTM(128, return_sequences=False, dropout=0.3, recurrent_dropout=0.3)),
        Dense(128, activation='relu'),
        Dropout(0.3),
        Dense(len(set(y)), activation='softmax')
    ])

    model.compile(
        loss='sparse_categorical_crossentropy',
        optimizer='adam',
        metrics=['accuracy']
    )

    model.fit(X, y, epochs=epochs, verbose=1)

    # Save
    model.save(os.path.join(MODEL_DIR, "main_model.h5"))
    pickle.dump(tokenizer, open(os.path.join(MODEL_DIR, "tokenizer_main.pkl"), "wb"))
    pickle.dump(le, open(os.path.join(MODEL_DIR, "label_main.pkl"), "wb"))

    print(f"✅ Model utama selesai dilatih ({len(questions)} data, vocab {len(tokenizer.word_index)})")
    return {"samples": len(questions), "vocab": len(tokenizer.word_index)}


# ==============================================================  
# 🔹 TRAIN FALLBACK MODEL (TF-IDF Semantic Search)
# ==============================================================
def retrain_fallback_from_db():
    with app.app_context():
        regs = Peraturan.query.all()
        if not regs:
            raise ValueError("❌ Tabel Peraturan kosong — upload PDF dulu.")

        # Ambil seluruh isi pasal
        contents = [r.sentence for r in regs]

    vectorizer = TfidfVectorizer()
    matrix = vectorizer.fit_transform(contents)

    pickle.dump(contents, open(os.path.join(MODEL_DIR, "fallback_texts.pkl"), "wb"))
    pickle.dump(vectorizer, open(os.path.join(MODEL_DIR, "fallback_vectorizer.pkl"), "wb"))
    pickle.dump(matrix, open(os.path.join(MODEL_DIR, "fallback_matrix.pkl"), "wb"))

    print(f"✅ Semantic fallback selesai dilatih ({len(contents)} pasal).")
    return {"pasal": len(contents)}


# ==============================================================  
# 🔹 TRAIN ALL
# ==============================================================
def retrain_all():
    print("\n🧠 Melatih ulang model utama (Dataset)...")
    retrain_main_from_db()

    print("\n📘 Melatih ulang semantic-fallback (Peraturan)...")
    retrain_fallback_from_db()

    print("\n🎉 Semua model selesai dilatih dan disimpan di folder model/")


if __name__ == "__main__":
    retrain_all()
