from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# Database configuration
DATABASE_CONFIG = {
    'SQLALCHEMY_DATABASE_URI': 'sqlite:///estate_management.db',
    'SQLALCHEMY_TRACK_MODIFICATIONS': False
}