import os
import pandas as pd
import re
from backend.config import app, db, UPLOADS_DIR
from backend.db.models import Dataset, Peraturan

# Folder upload
DATASET_PATH = os.path.join(UPLOADS_DIR, "datasets")
TEXT_PATH = os.path.join(UPLOADS_DIR, "texts")

def load_dataset_to_db(file_path: str = None, remove_file: bool = True):
    if file_path is None:
        dataset_files = [f for f in os.listdir(DATASET_PATH) if f.endswith(".csv")]
        if not dataset_files:
            raise FileNotFoundError("❌ Tidak ada file CSV di uploads/datasets/")
        file_path = os.path.join(DATASET_PATH, dataset_files[0])

    print(f"📄 Membaca dataset: {file_path}")
    # Try common encodings to avoid UnicodeDecodeError on various CSVs
    read_errors = []
    encodings_to_try = ["utf-8-sig", "utf-8", "latin1"]
    data = None
    used_encoding = None
    skipped_rows = 0

    for enc in encodings_to_try:
        # First try the default C engine reading
        try:
            data = pd.read_csv(file_path, encoding=enc)
            used_encoding = enc
            print(f"Berhasil membaca CSV dengan encoding: {enc} (C engine)")
            break
        except Exception as e:
            read_errors.append((enc, f"C engine: {e}"))
        # Try python engine with automatic separator detection
        try:
            data = pd.read_csv(file_path, encoding=enc, sep=None, engine='python')
            used_encoding = enc
            print(f"ℹ️ Berhasil membaca CSV dengan encoding: {enc} (python engine, sep auto-detect)")
            break
        except Exception as e:
            read_errors.append((enc, f"python engine sep auto: {e}"))
        # Try skipping bad lines (pandas >=1.3 supports on_bad_lines)
        try:
            data = pd.read_csv(file_path, encoding=enc, sep=None, engine='python', on_bad_lines='skip')
            used_encoding = enc
            print(f"⚠️ CSV dibaca dengan skipping bad lines using encoding: {enc}")
            # compute skipped rows approximately
            try:
                total_lines = sum(1 for _ in open(file_path, 'r', encoding=enc, errors='replace'))
                # subtract header line
                skipped_rows = max(0, total_lines - 1 - len(data))
            except Exception:
                skipped_rows = 0
            break
        except Exception as e:
            read_errors.append((enc, f"python engine skip: {e}"))

    if data is None:
        err_msgs = "; ".join([f"{enc}:{msg}" for enc, msg in read_errors])
        raise ValueError(f"Gagal membaca CSV. Attempts: {err_msgs}")

    if "pertanyaan" not in data.columns or "jawaban" not in data.columns:
        raise ValueError("❌ CSV harus punya kolom: pertanyaan, jawaban")

    with app.app_context():
        # Hapus entri lama sebelum memasukkan yang baru
        db.session.query(Dataset).delete()
        for _, row in data.iterrows():
            item = Dataset(pertanyaan=row["pertanyaan"], jawaban=row["jawaban"])
            db.session.add(item)
        db.session.commit()
        inserted = len(data)
        print(f"✅ {inserted} baris dataset berhasil dimasukkan ke tabel 'dataset'.")

    if remove_file:
        try:
            processed_basename = os.path.basename(file_path)
            if os.path.isdir(DATASET_PATH):
                for f in os.listdir(DATASET_PATH):
                    if not f.lower().endswith('.csv'):
                        continue
                    if f == processed_basename:
                        # skip the file that was just uploaded/processed
                        continue
                    fp = os.path.join(DATASET_PATH, f)
                    try:
                        os.remove(fp)
                        print(f"🗑️ File dataset lama dihapus: {fp}")
                    except Exception as sub_e:
                        print(f"⚠️ Gagal menghapus file dataset {fp}: {sub_e}")
            else:
                # fallback: try removing only the specific file_path
                try:
                    os.remove(file_path)
                    print(f"🗑️ File dataset dihapus (fallback): {file_path}")
                except Exception as sub_e:
                    print(f"⚠️ Gagal menghapus file dataset fallback {file_path}: {sub_e}")
        except Exception as e:
            print(f"⚠️ Gagal saat proses penghapusan file dataset: {e}")

    return inserted, skipped_rows

def load_peraturan_to_db():
    text_files = [f for f in os.listdir(TEXT_PATH) if f.endswith(".txt")]
    if not text_files:
        raise FileNotFoundError("❌ Tidak ada file hasil parsing PDF/Word di uploads/texts/")
    
    text_file = os.path.join(TEXT_PATH, text_files[0])
    filename = os.path.basename(text_file)

    print(f"📘 Membaca file peraturan: {text_file}")

    # Baca seluruh teks
    with open(text_file, "r", encoding="utf-8") as f:
        raw_text = f.read()

    def split_sentences(text: str) -> list:
        sentences = re.split(r'(?<=[.!?])\s+', text.strip())
        sentences = [s.strip() for s in sentences if s.strip()]
        return sentences

    sentences_list = split_sentences(raw_text)

    with app.app_context():
        db.session.query(Peraturan).delete()

        for idx, sentence in enumerate(sentences_list, 1):
            entry = Peraturan(
                sentence_number=idx,
                sentence=sentence,
                filename=filename
            )
            db.session.add(entry)

        db.session.commit()

    print(f"✅ {len(sentences_list)} kalimat berhasil dimasukkan ke tabel 'peraturan'.")


if __name__ == "__main__":
    print("🚀 Memulai proses load dataset & peraturan ke database...")
    try:
        inserted = load_dataset_to_db()
        print(f"🎉 {inserted} baris dataset dimasukkan ke database")
    except Exception as e:
        print(f"❌ Error load dataset: {e}")

    try:
        load_peraturan_to_db()
    except Exception as e:
        print(f"❌ Error load peraturan: {e}")
    print("Selesai")
