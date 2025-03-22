import os
import logging
from flask import Flask, render_template, jsonify, request
from flask_sqlalchemy import SQLAlchemy

# 🔹 Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 🔹 Initialize Flask App
app = Flask(__name__)

# 🔹 Database Configuration (PostgreSQL for Railway, SQLite for Local)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///database/sparks.db")

if DATABASE_URL.startswith("postgres://"):  
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://")  # Fix for SQLAlchemy

app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.secret_key = os.getenv("SESSION_SECRET", "default-secret-key")

# 🔹 Ensure Database Folder Exists (For SQLite)
if "sqlite" in DATABASE_URL:
    os.makedirs("database", exist_ok=True)

# 🔹 Initialize Database
db = SQLAlchemy(app)

with app.app_context():
    db.create_all()
    logger.info("✅ Database initialized and tables created.")

# 🔹 Request Logging (For Debugging)
@app.before_request
def log_request():
    logger.info(f"📥 Incoming Request: {request.method} {request.path}")

# 🔹 API Routes
@app.route('/api/status')
def api_status():
    return jsonify({'status': 'ok', 'message': 'Anime Card Battle API is running!', 'version': '1.0.0'})

@app.route('/api/cards')
def api_cards():
    from models import Card
    cards = Card.query.all()
    return jsonify([card.to_dict() for card in cards])

@app.route('/api/players')
def api_players():
    from models import Player
    players = Player.query.all()
    return jsonify([player.to_dict() for player in players])

# 🔹 Web Routes
@app.route('/')
def home():
    from models import Player, Card
    top_players = Player.query.order_by(Player.level.desc()).limit(5).all()
    rare_cards = Card.query.filter(Card.rarity.in_(['Legendary', 'Epic'])).limit(4).all()
    return render_template('home.html', title='Sparks - Home', top_players=top_players, rare_cards=rare_cards)

# 🔹 Error Handlers
@app.errorhandler(404)
def page_not_found(e):
    logger.warning(f"⚠️ 404 Not Found: {request.path}")
    return render_template('404.html', title='Page Not Found'), 404

@app.errorhandler(500)
def server_error(e):
    logger.error(f"🔥 500 Internal Server Error: {str(e)}")
    return render_template('500.html', title='Server Error'), 500

# 🔹 Run the App
if __name__ == "__main__":
    from waitress import serve
    port = int(os.getenv("PORT", 5000))
    logger.info(f"🚀 Starting server on port {port}...")
    serve(app, host="0.0.0.0", port=port)