from datetime import datetime
from typing import List

from flask_login import UserMixin
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, Boolean, DateTime, ForeignKey, Enum
from enum import Enum as PyEnum

from . import db


# -------------------------
# ENUM
# -------------------------
class ProposalStatus(PyEnum):
    open = 1
    closed_to_new_participants = 2
    finalized = 3
    cancelled = 4


# -------------------------
# USER
# -------------------------
class User(UserMixin, db.Model):
    id = mapped_column(Integer, primary_key=True)
    email = mapped_column(String(255), unique=True, nullable=False)
    name = mapped_column(String(120), nullable=False)
    bio = mapped_column(String(500))
    password_hash = mapped_column(String(255), nullable=False)

    created_at = mapped_column(DateTime, default=datetime.utcnow)
    updated_at = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    participants = relationship("TripProposalParticipant", back_populates="user")


# -------------------------
# LOCATION
# -------------------------
class Location(db.Model):
    id = mapped_column(Integer, primary_key=True)
    name = mapped_column(String(120), nullable=False)


# -------------------------
# ACTIVITY
# -------------------------
class Activity(db.Model):
    id = mapped_column(Integer, primary_key=True)
    name = mapped_column(String(120), nullable=False)
    trip_id: Mapped[int] = mapped_column(ForeignKey("tripproposal.id"))
    trip: Mapped["TripProposal"] = relationship("TripProposal", back_populates="activities", foreign_keys=[trip_id])


# -------------------------
# TRIP
# -------------------------
class TripProposal(db.Model):
    __tablename__ = 'tripproposal'
    id = mapped_column(Integer, primary_key=True)
    name = mapped_column(String(120))
    budget = mapped_column(Integer)
    max_members = mapped_column(Integer)
    status = mapped_column(Enum(ProposalStatus), default=ProposalStatus.open)

    departure_id = mapped_column(ForeignKey("location.id"))
    destination_id = mapped_column(ForeignKey("location.id"))

    departure_location = relationship("Location", foreign_keys=[departure_id])
    destination_location = relationship("Location", foreign_keys=[destination_id])

    activities: Mapped[list["Activity"]] = relationship("Activity", back_populates="trip")

    participants = relationship("TripProposalParticipant", back_populates="trip")


# -------------------------
# PARTICIPANTS
# -------------------------
class TripProposalParticipant(db.Model):
    id = mapped_column(Integer, primary_key=True)

    user_id = mapped_column(ForeignKey("user.id"))
    trip_id = mapped_column(ForeignKey("tripproposal.id"))

    can_edit = mapped_column(Boolean, default=False)

    user = relationship("User", back_populates="participants")
    trip = relationship("TripProposal", back_populates="participants")
