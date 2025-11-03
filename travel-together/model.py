import datetime
from typing import List

from sqlalchemy import String, DateTime, ForeignKey, Integer, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

import flask_login


from . import db

import enum

class User(flask_login.UserMixin, db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(128), unique=True)
    name: Mapped[str] = mapped_column(String(64))
    password: Mapped[str] = mapped_column(String(256))
    description: Mapped[str] = mapped_column(String(256))
    messages: Mapped[List["Message"]] = relationship(back_populates="Message")

class TripProposal(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    departures: Mapped[List["Location"]] = relationship(back_populates="Location")
    destinationId:  Mapped[int] = mapped_column(ForeignKey("Location.id"))
    destination: Mapped["Location"] = relationship(back_populates="Location")
    possibleDates: Mapped[List["DateProposal"]] = relationship(back_populates="Location")
    budget: Mapped[int] = mapped_column(Integer)
    activities: Mapped[List["Activity"]] = relationship(back_populates="Activity")
    maxMembers: Mapped[int] = mapped_column(Integer)
    status: Mapped["ProposalStatus"]
    messages: Mapped[List["Message"]] = relationship(back_populates="Message")
    departures_final: Mapped[bool] = mapped_column(Boolean)
    destination_final: Mapped[bool] = mapped_column(Boolean)
    possibleDates_final: Mapped[bool] = mapped_column(Boolean)
    activities_final: Mapped[bool] = mapped_column(Boolean)

class Message(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    text: Mapped[str] = mapped_column(String(256))
    timestamp: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    authorId: Mapped[int] = mapped_column(ForeignKey("TripProposalParticipant.id"))
    author: Mapped["TripProposalParticipant"] = relationship(back_populates="TripProposalParticipant")


class TripProposalParticipant(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    userId: Mapped[int] = mapped_column(ForeignKey("User.id"))
    user: Mapped["User"] = relationship(back_populates="User")
    tripId: Mapped[int] = mapped_column(ForeignKey("TripProposal.id"))
    trip: Mapped["TripProposal"] = relationship(back_populates="TripProposal")
    canEdit: Mapped[bool] = mapped_column(Boolean)

class Meetup(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    meetupTime: Mapped[datetime.datetime] = mapped_column(DateTime)
    locationId: Mapped[int] = mapped_column(ForeignKey("Location.id"))
    location: Mapped["Location"] = relationship(back_populates="Location")
    tripId: Mapped[int] = mapped_column(ForeignKey("TripProposal.id"))
    trip: Mapped["TripProposal"] = relationship(back_populates="TripProposal")
    createdById: Mapped[int] = mapped_column(ForeignKey("User.id"))
    createdBy: Mapped["User"] = relationship(back_populates="User")

class Activity(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(64))
    description: Mapped[str] = mapped_column(String(256))

class Location(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(64))


class DateProposal(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    dateFrom: Mapped[datetime.datetime] = mapped_column(DateTime)
    dateTo: Mapped[datetime.datetime] = mapped_column(DateTime)


class ProposalStatus(enum.Enum):
    open = 1
    closed_to_new_participants = 2
    finalized = 3
    cancelled = 4
