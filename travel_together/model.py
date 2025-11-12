from datetime import datetime
from flask_login import UserMixin
from sqlalchemy.sql import func
from . import db


class User(UserMixin, db.Model):
    id = db.mapped_column(db.Integer, primary_key=True)
    email = db.mapped_column(db.String(255), unique=True, nullable=False)
    name = db.mapped_column(db.String(120), nullable=False)
    bio = db.mapped_column(db.String(500), nullable=True)
    password_hash = db.mapped_column(db.String(255), nullable=False)

    created_at = db.mapped_column(
        db.DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at = db.mapped_column(
        db.DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    def __repr__(self):
        return f"<User {self.name}>"


class Post(db.Model):
    id = db.mapped_column(db.Integer, primary_key=True)
    text = db.mapped_column(db.String(500), nullable=False)
    timestamp = db.mapped_column(db.DateTime(timezone=True), server_default=func.now())
    user_id = db.mapped_column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    response_to_id = db.mapped_column(db.Integer, db.ForeignKey("post.id"), nullable=True)

    user = db.relationship("User", backref="posts")
    response_to = db.relationship("Post", remote_side=[id], backref="responses")
