import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__)

DB_USER = "root"
DB_PASS = ""           
DB_HOST = "localhost"
DB_NAME = "chatbot_db"

app.config["SQLALCHEMY_DATABASE_URI"] = f"mysql+mysqlconnector://{DB_USER}:{DB_PASS}@{DB_HOST}/{DB_NAME}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = "change_this_secret"

db = SQLAlchemy(app)
MODEL_DIR = os.path.join(BASE_DIR, "model")
UPLOADS_DIR = os.path.join(BASE_DIR, "uploads")
os.makedirs(MODEL_DIR, exist_ok=True)
os.makedirs(os.path.join(UPLOADS_DIR, "datasets"), exist_ok=True)
os.makedirs(os.path.join(UPLOADS_DIR, "pdfs"), exist_ok=True)
