import os
from flask import Flask, render_template, jsonify, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Define database model base
class Base(DeclarativeBase):
    pass

# Create Flask app
app = Flask(__name__)

# Ensure the database directory exists
db_path = os.path.abspath("database/sparks.db")  # Absolute path to SQLite file
os.makedirs(os.path.dirname(db_path), exist_ok=True)  # Create database folder if missing

# Configure SQLAlchemy for SQLite
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"  # ✅ Use SQLite
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False  # Reduce warnings
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {"poolclass": None}  # ✅ Disable pooling for SQLite
app.secret_key = os.environ.get("SESSION_SECRET", "default-development-key")

# Initialize database
db = SQLAlchemy(model_class=Base)
db.init_app(app)

# Ensure database tables exist
with app.app_context():
    import models  # Import models
    db.create_all()
    logger.info("✅ Database tables created or verified.")

# API Routes
@app.route('/api/status')
def api_status():
    return jsonify({
        'status': 'ok',
        'message': 'Anime Card Battle API is running!',
        'version': '1.0.0'
    })

@app.route('/api/cards')
def api_cards():
    from models import Card
    cards = Card.query.all()
    return jsonify([card.to_dict() for card in cards])

@app.route('/api/cards/<int:card_id>')
def api_card_detail(card_id):
    from models import Card
    card = Card.query.get_or_404(card_id)
    return jsonify(card.to_dict())

@app.route('/api/players')
def api_players():
    from models import Player
    players = Player.query.all()
    return jsonify([player.to_dict() for player in players])

@app.route('/api/players/<int:player_id>')
def api_player_detail(player_id):
    from models import Player, UserCard
    player = Player.query.get_or_404(player_id)
    cards = UserCard.query.filter_by(player_id=player_id).all()
    return jsonify({
        **player.to_dict(),
        "cards": [card.to_dict() for card in cards]
    })

# Web Routes
@app.route('/')
def home():
    from models import Player, Card
    top_players = Player.query.order_by(Player.level.desc()).limit(5).all()
    rare_cards = Card.query.filter(Card.rarity.in_(['Legendary', 'Epic'])).limit(4).all()
    return render_template('home.html', title='Anime Card Game - Home', top_players=top_players, rare_cards=rare_cards)

@app.route('/cards')
def cards():
    from models import Card
    cards = Card.query.all()
    return render_template('cards.html', title='Card Collection', cards=cards)

@app.route('/cards/<int:card_id>')
def card_detail(card_id):
    from models import Card
    card = Card.query.get_or_404(card_id)
    return render_template('card_detail.html', title=f'Card - {card.name}', card=card)

@app.route('/players')
def players():
    from models import Player
    players = Player.query.all()
    return render_template('players.html', title='Players', players=players)

@app.route('/players/<int:player_id>')
def player_detail(player_id):
    from models import Player, UserCard
    player = Player.query.get_or_404(player_id)
    cards = UserCard.query.filter_by(player_id=player_id).all()
    return render_template('player_detail.html', title=f'Player - {player.username}', player=player, cards=cards)

# Error Handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html', title='Page Not Found'), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('500.html', title='Server Error'), 500

# Run the app
if __name__ == "__main__":
    from waitress import serve
    serve(app, host="0.0.0.0", port=5000)