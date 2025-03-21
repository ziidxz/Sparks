from flask_sqlalchemy import SQLAlchemy

# Create the database instance (moved from app.py)
db = SQLAlchemy()

class Player(db.Model):
    __tablename__ = 'api_players'
    id = db.Column(db.Integer, primary_key=True)
    discord_id = db.Column(db.BigInteger, unique=True, nullable=False)
    username = db.Column(db.String(128), nullable=False)
    gold = db.Column(db.Integer, default=1000)
    diamonds = db.Column(db.Integer, default=0)
    level = db.Column(db.Integer, default=1)
    xp = db.Column(db.Integer, default=0)
    wins = db.Column(db.Integer, default=0)
    losses = db.Column(db.Integer, default=0)
    pvp_wins = db.Column(db.Integer, default=0)
    pvp_losses = db.Column(db.Integer, default=0)

    def __repr__(self):
        return f'<Player {self.username}>'

    def to_dict(self):
        return {
            'id': self.id,
            'discord_id': self.discord_id,
            'username': self.username,
            'gold': self.gold,
            'diamonds': self.diamonds,
            'level': self.level,
            'xp': self.xp,
            'wins': self.wins,
            'losses': self.losses,
            'pvp_wins': self.pvp_wins,
            'pvp_losses': self.pvp_losses
        }

class Card(db.Model):
    __tablename__ = 'api_cards'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    rarity = db.Column(db.String(20), nullable=False)
    attack = db.Column(db.Integer, nullable=False)
    defense = db.Column(db.Integer, nullable=False)
    speed = db.Column(db.Integer, nullable=False)
    element = db.Column(db.String(20), nullable=False)
    skill = db.Column(db.String(100), nullable=False)
    skill_description = db.Column(db.Text, nullable=False)
    image_url = db.Column(db.String(255))

    def __repr__(self):
        return f'<Card {self.name}>'

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'rarity': self.rarity,
            'attack': self.attack,
            'defense': self.defense,
            'speed': self.speed,
            'element': self.element,
            'skill': self.skill,
            'skill_description': self.skill_description,
            'image_url': self.image_url
        }

class UserCard(db.Model):
    __tablename__ = 'api_user_cards'
    id = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.Integer, db.ForeignKey('api_players.id'), nullable=False)
    card_id = db.Column(db.Integer, db.ForeignKey('api_cards.id'), nullable=False)
    level = db.Column(db.Integer, default=1)
    xp = db.Column(db.Integer, default=0)
    equipped = db.Column(db.Boolean, default=False)

    player = db.relationship('Player', backref=db.backref('cards', lazy=True))
    card = db.relationship('Card')

    def __repr__(self):
        return f'<UserCard {self.id}>'

    def to_dict(self):
        return {
            'id': self.id,
            'player_id': self.player_id,
            'card_id': self.card_id,
            'card': self.card.to_dict() if self.card else None,
            'level': self.level,
            'xp': self.xp,
            'equipped': self.equipped
        }