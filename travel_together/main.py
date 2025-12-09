from urllib import request

from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from .model import *

bp = Blueprint("main", __name__, url_prefix="/")


@bp.route("/")
@login_required
def index():
    return render_template("main/index.html", user=current_user)

@bp.route("/allTrips")
@login_required
def allTrips():
    query = db.select(TripProposal)

    trip_proposals = db.session.execute(query).scalars().all()
    return render_template("main/landingPage.html", trip_proposals=trip_proposals)


@bp.route("/profile/<int:user_id>")
@login_required
def profile(user_id):
    query = db.select(User).where(User.id == user_id)
    user = db.session.execute(query).one()
    return render_template("user/profile.html", user=user)

@bp.route("/edit_profile")
@login_required
def edit_profile():
    return render_template("user/edit_profile.html", user=current_user)


@bp.route("/createTrip", methods=["GET", "POST"])
@login_required
def createTrip():
    if request.method == "POST":
        name = request.form["name"]
        budget = request.form["budget"]
        maxMembers = request.form["maxMembers"]

        newTrip = TripProposal(name=name, budget=budget, maxMembers=maxMembers, status=ProposalStatus.open, departures_final=False, destination_final=False, possibleDates_final=False, activities_final=False)
        db.session.add(newTrip)
        db.session.commit()
        flash("trip created successfully")
        return render_template("main/index.html", user=current_user)

    return render_template("trips/createTrip.html")