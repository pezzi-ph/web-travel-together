import datetime
from typing import List, Optional

from sqlalchemy import String, DateTime, ForeignKey, Integer, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from . import db

import enum

class User(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(128), unique=True)
    name: Mapped[str] = mapped_column(String(64))
    password: Mapped[str] = mapped_column(String(256))
    description: Mapped[str] = mapped_column(String(256))
    messages: Mapped[List["Message"]] = relationship(back_populates="Message")

class TripProposal(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    departures: Mapped[List["Location"]] = relationship(back_populates="Location")
    destination:  Mapped[int] = mapped_column(ForeignKey("Location.id"))
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
    timestamp: Mapped[datetime.datetime] = mapped_column(DateTime)
    author: Mapped[int] = mapped_column(ForeignKey("User.id"))
    trip: Mapped[int] = mapped_column(ForeignKey("TripProposal.id"))

class TripProposalParticipant(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    user: Mapped[int] = mapped_column(ForeignKey("User.id"))
    trip: Mapped[int] = mapped_column(ForeignKey("TripProposal.id"))
    canEdit: Mapped[bool] = mapped_column(Boolean)

class Meetup(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    meetupTime: Mapped[datetime.datetime] = mapped_column(DateTime)
    location: Mapped[int] = mapped_column(ForeignKey("Location.id"))
    trip: Mapped[int] = mapped_column(ForeignKey("TripProposal.id"))
    createdBy: Mapped[int] = mapped_column(ForeignKey("User.id"))

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
