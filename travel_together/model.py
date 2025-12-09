import enum
from datetime import datetime
from typing import List
from flask_login import UserMixin
from sqlalchemy import Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
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




class ProposalStatus(enum.Enum):
    open = 1
    closed_to_new_participants = 2
    finalized = 3
    cancelled = 4

class Location(db.Model):
    id: Mapped[int] =db.mapped_column(primary_key=True)
    name: Mapped[str] =db.mapped_column(db.String(64))
    trip_destinations: Mapped[List["TripProposal"]] = db.relationship(back_populates="destination")

class TripProposal(db.Model):
    id: Mapped[int] =db.mapped_column(primary_key=True)
    name: Mapped[str] = db.mapped_column(db.String(64))
    budget: Mapped[int] =db.mapped_column(db.Integer)
    maxMembers: Mapped[int] =db.mapped_column(db.Integer)
    destinationId:  Mapped[int] =db.mapped_column(db.ForeignKey("location.id"))
    destination: Mapped["Location"] = db.relationship(back_populates="trip_destinations")
    status: Mapped["ProposalStatus"]
    """
        departures: Mapped[List["Location"]] = db.relationship(back_populates="Location")
        possibleDates: Mapped[List["DateProposal"]] = db.relationship(back_populates="Location")
        activities: Mapped[List["Activity"]] = db.relationship(back_populates="Activity")
        messages: Mapped[List["Message"]] = db.relationship(back_populates="Message")
    """
    departures_final: Mapped[bool] =db.mapped_column(db.Boolean)
    destination_final: Mapped[bool] =db.mapped_column(db.Boolean)
    possibleDates_final: Mapped[bool] =db.mapped_column(db.Boolean)
    activities_final: Mapped[bool] =db.mapped_column(db.Boolean)


class TripProposalParticipant(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    userId: Mapped[int] = mapped_column(ForeignKey("user.id"))
    user: Mapped["User"] = relationship("User")
    tripId: Mapped[int] = mapped_column(ForeignKey("trip_proposal.id"))
    trip: Mapped["TripProposal"] = relationship("TripProposal")
    canEdit: Mapped[bool] = mapped_column(Boolean)

"""
class Meetup(db.Model):
    id: Mapped[int] =db.mapped_column(primary_key=True)
    meetupTime: Mapped[datetime.datetime] =db.mapped_column(db.DateTime(timezone=True))
    locationId: Mapped[int] =db.mapped_column(db.ForeignKey("Location.id"))
    location: Mapped["Location"] = db.relationship(back_populates="Location")
    tripId: Mapped[int] =db.mapped_column(db.ForeignKey("TripProposal.id"))
    trip: Mapped["TripProposal"] = db.relationship(back_populates="TripProposal")
    createdById: Mapped[int] =db.mapped_column(db.ForeignKey("User.id"))
    createdBy: Mapped["User"] = db.relationship(back_populates="User")

class Activity(db.Model):
    id: Mapped[int] =db.mapped_column(primary_key=True)
    name: Mapped[str] =db.mapped_column(db.String(64))
    description: Mapped[str] =db.mapped_column(db.String(256))


class DateProposal(db.Model):
    id: Mapped[int] =db.mapped_column(primary_key=True)
    dateFrom: Mapped[datetime.datetime] =db.mapped_column(db.DateTime(timezone=True))
    dateTo: Mapped[datetime.datetime] =db.mapped_column(db.DateTime(timezone=True))

"""
