import os
import logging
from flask import Flask, render_template, jsonify, request
from models import db, Player, Card, UserCard  # Import db AFTER defining it in models.py

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Ensure the database directory exists (only for SQLite)
db_path = os.path.abspath("database/sparks.db")
if not os.path.exists(os.path.dirname(db_path)):
    os.makedirs(os.path.dirname(db_path))

# Set Database URI (SQLite for local, PostgreSQL for Railway)
DATABASE_URL = os.environ.get("DATABASE_URL", f"sqlite:///{db_path}")
if DATABASE_URL.startswith("postgres://"):  
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://")  # Fix for SQLAlchemy

app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.secret_key = os.environ.get("SESSION_SECRET", "default-secret-key")

# Initialize database with Flask app
db.init_app(app)

# Ensure database tables exist
with app.app_context():
    db.create_all()
    logger.info("✅ Database tables created or verified.")

# Log each request (For Railway debugging)
@app.before_request
def log_request():
    logger.info(f"Incoming Request: {request.method} {request.path}")

# API Routes
@app.route('/api/status')
def api_status():
    return jsonify({'status': 'ok', 'message': 'Anime Card Battle API is running!', 'version': '1.0.0'})

@app.route('/api/cards')
def api_cards():
    cards = Card.query.all()
    return jsonify([card.to_dict() for card in cards])

@app.route('/api/cards/<int:card_id>')
def api_card_detail(card_id):
    card = Card.query.get_or_404(card_id)
    return jsonify(card.to_dict())

@app.route('/api/players')
def api_players():
    players = Player.query.all()
    return jsonify([player.to_dict() for player in players])

@app.route('/api/players/<int:player_id>')
def api_player_detail(player_id):
    player = Player.query.get_or_404(player_id)
    cards = UserCard.query.filter_by(player_id=player_id).all()
    return jsonify({'player': player.to_dict(), 'cards': [card.to_dict() for card in cards]})

# Web Routes
@app.route('/')
def home():
    top_players = Player.query.order_by(Player.level.desc()).limit(5).all()
    rare_cards = Card.query.filter(Card.rarity.in_(['Legendary', 'Epic'])).limit(4).all()
    return render_template('home.html', title='Anime Card Game - Home', top_players=top_players, rare_cards=rare_cards)

@app.route('/cards')
def cards():
    all_cards = Card.query.all()
    return render_template('cards.html', title='Card Collection', cards=all_cards)

@app.route('/players')
def players():
    all_players = Player.query.all()
    return render_template('players.html', title='Players', players=all_players)

# Error Handlers
@app.errorhandler(404)
def page_not_found(e):
    logger.warning(f"404 Not Found: {request.path}")
    return render_template('404.html', title='Page Not Found'), 404

@app.errorhandler(500)
def server_error(e):
    logger.error(f"500 Internal Server Error: {str(e)}")
    return render_template('500.html', title='Server Error'), 500

# Run the app
if __name__ == "__main__":
    from waitress import serve
    port = int(os.environ.get("PORT", 5000))  # Use Railway's assigned port
    logger.info(f"🚀 Starting server on port {port}...")
    serve(app, host="0.0.0.0", port=port)