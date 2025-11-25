from flask import request
from flask_cors import CORS
from backend.config import app, db
from backend.routes.user_routes import user_bp
from backend.routes.chatbot_routes import chat_bp
from backend.routes.admin_routes import admin_bp

CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

app.register_blueprint(user_bp, url_prefix="/api")
app.register_blueprint(chat_bp, url_prefix="/api")
app.register_blueprint(admin_bp, url_prefix="/api/admin")

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5000)
