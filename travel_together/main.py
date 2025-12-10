from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    request,
    abort,
    flash,
)
from flask_login import login_required, current_user

from . import db
from .model import (
    User,
    TripProposal,
    TripProposalParticipant,
    Location,
    ProposalStatus, Activity, Message, PossibleDates,
)

bp = Blueprint("main", __name__)

# ---------------------------------------------------------
# HOME PAGE
# ---------------------------------------------------------
@bp.route("/")
@login_required
def index():
    trips = db.session.execute(db.select(TripProposal)).scalars().all()
    return render_template("main/index.html", trips=trips)


# ---------------------------------------------------------
# USER PROFILE
# ---------------------------------------------------------
@bp.route("/profile/<int:user_id>")
@login_required
def profile(user_id):
    user = db.session.get(User, user_id)
    if user is None:
        abort(404)

    return render_template("user/profile.html", user=user)


# ---------------------------------------------------------
# EDIT PROFILE
# ---------------------------------------------------------
@bp.route("/profile/<int:user_id>/edit", methods=["GET", "POST"])
@login_required
def edit_profile(user_id):
    user = db.session.get(User, user_id)
    if user is None:
        abort(404)

    # Only the owner can edit
    if user.id != current_user.id:
        abort(403)

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        bio = request.form.get("bio", "").strip()

        if not name:
            flash("Name cannot be empty.")
            return render_template("user/edit_profile.html", user=user)

        user.name = name
        user.bio = bio
        db.session.commit()

        flash("Profile updated successfully.")
        return redirect(url_for("main.profile", user_id=user.id))

    return render_template("user/edit_profile.html", user=user)


# ---------------------------------------------------------
# CREATE TRIP PROPOSAL
# ---------------------------------------------------------
@bp.route("/trips/new", methods=["GET", "POST"])
@login_required
def create_trip():
    if request.method == "POST":
        name = request.form.get("name")
        departure = request.form.get("departure")
        destination = request.form.get("destination")
        budget = request.form.get("budget")
        max_members = request.form.get("max_members")
        activities = request.form.getlist("activities[]")
        possible_departure_dates = request.form.getlist("possible_departure_dates[]")
        possible_return_dates = request.form.getlist("possible_return_dates[]")

        new_dates = []
        for i, departure_date in enumerate(possible_departure_dates):
            if departure_date > possible_return_dates[i]:
                flash("Departure date cannot be after return date.")
                return redirect(url_for("main.create_trip"))
            new_dates.append(PossibleDates(departure_date=departure_date, return_date=possible_return_dates[i]))

        activities_new = []
        for activity in activities:
            if len(activity) < 1:
                continue
            activities_new.append(Activity(name=activity))

        # Validate fields
        if not name or not departure or not destination:
            flash("Name, departure, and destination are required.")
            return redirect(url_for("main.create_trip"))

        # Create or get departure location
        dep_loc = Location.query.filter_by(name=departure).first()
        if not dep_loc:
            dep_loc = Location(name=departure)
            db.session.add(dep_loc)

        # Create or get destination location
        dest_loc = Location.query.filter_by(name=destination).first()
        if not dest_loc:
            dest_loc = Location(name=destination)
            db.session.add(dest_loc)

        # Create trip
        trip = TripProposal(
            name=name,
            departure_location=dep_loc,
            destination_location=dest_loc,
            budget=int(budget) if budget else 0,
            max_members=int(max_members),
            status=ProposalStatus.open,
            activities=activities_new,
            possible_dates=new_dates,
        )
        db.session.add(trip)
        db.session.commit()

        # Add creator as participant (editor)
        creator = TripProposalParticipant(
            user=current_user,
            trip=trip,
            can_edit=True,
        )
        db.session.add(creator)
        db.session.commit()

        flash("Trip created successfully!")
        return redirect(url_for("main.trip_detail", trip_id=trip.id))

    return render_template("trips/create_trip.html", trip=TripProposal())


# ---------------------------------------------------------
# TRIP DETAIL PAGE
# ---------------------------------------------------------
@bp.route("/trips/<int:trip_id>")
@login_required
def trip_detail(trip_id):
    trip = TripProposal.query.get_or_404(trip_id)

    # Check if user is participant
    is_participant = any(p.user_id == current_user.id for p in trip.participants)

    can_edit = any(p.user_id == current_user.id and p.can_edit for p in trip.participants)

    # Check capacity
    current_count = len(trip.participants)
    is_full = current_count >= trip.max_members

    can_join = (
        (not is_participant)
        and (trip.status == ProposalStatus.open)
        and (not is_full)
    )

    return render_template(
        "trips/trip_detail.html",
        trip=trip,
        is_participant=is_participant,
        is_full=is_full,
        can_join=can_join,
        can_edit=can_edit
    )


# ---------------------------------------------------------
# JOIN A TRIP
# ---------------------------------------------------------
@bp.route("/trips/<int:trip_id>/join", methods=["POST"])
@login_required
def join_trip(trip_id):
    trip = TripProposal.query.get_or_404(trip_id)

    # Must be open
    if trip.status != ProposalStatus.open:
        flash("This trip is not open to new participants.")
        return redirect(url_for("main.trip_detail", trip_id=trip.id))

    # Already participating?
    existing = TripProposalParticipant.query.filter_by(
        trip_id=trip.id, user_id=current_user.id
    ).first()
    if existing:
        flash("You are already participating in this trip.")
        return redirect(url_for("main.trip_detail", trip_id=trip.id))

    # Check capacity
    current_count = TripProposalParticipant.query.filter_by(trip_id=trip.id).count()
    if current_count >= trip.max_members:
        flash("This trip is full.")
        return redirect(url_for("main.trip_detail", trip_id=trip.id))

    # Add participant
    participation = TripProposalParticipant(
        user=current_user,
        trip=trip,
        can_edit=False,
    )
    db.session.add(participation)
    db.session.commit()

    flash("You joined the trip!")
    return redirect(url_for("main.trip_detail", trip_id=trip.id))








# ---------------------------------------------------------
# Edit A TRIP
# ---------------------------------------------------------
@bp.route("/trips/<int:trip_id>/edit", methods=["GET", "POST"])
@login_required
def edit_trip(trip_id):
    stmt = db.select(TripProposalParticipant).where(TripProposalParticipant.trip_id == trip_id, TripProposalParticipant.user_id == current_user.id)
    participant = db.session.execute(stmt).scalar()
    if participant is None or not participant.can_edit:
        flash("You are not allowed to edit this trip.")
        return index()

    trip = TripProposal.query.get_or_404(trip_id)

    if request.method == "POST":
        name = request.form.get("name")
        departure = request.form.get("departure")
        destination = request.form.get("destination")
        budget = request.form.get("budget")
        max_members = request.form.get("max_members")
        activities = request.form.getlist("activities[]")
        possible_departure_dates = request.form.getlist("possible_departure_dates[]")
        possible_return_dates = request.form.getlist("possible_return_dates[]")
        status = request.form.get("status")

        new_dates = []
        for i, departure_date in enumerate(possible_departure_dates):
            if departure_date > possible_return_dates[i]:
                flash("Departure date cannot be after return date.")
                return redirect(url_for("main.create_trip"))
            new_dates.append(PossibleDates(departure_date=departure_date, return_date=possible_return_dates[i]))



        activities_new = []
        for activity in activities:
            if len(activity) < 1:
                continue
            act = Activity.query.filter_by(name=activity, trip_id=trip_id).first()
            activities_new.append(act or Activity(name=activity, trip_id=trip_id))

        # Validate fields
        if not name or not departure or not destination:
            flash("Name, departure, and destination are required.")
            return redirect(url_for("main.create_trip"))

        # Create or get departure location
        dep_loc = Location.query.filter_by(name=departure).first()
        if not dep_loc:
            dep_loc = Location(name=departure)
            db.session.add(dep_loc)

        # Create or get destination location
        dest_loc = Location.query.filter_by(name=destination).first()
        if not dest_loc:
            dest_loc = Location(name=destination)
            db.session.add(dest_loc)
        trip.name = name
        trip.departure_location = dep_loc
        trip.destination_location = dest_loc
        trip.budget = budget
        trip.max_members = max_members
        trip.activities = activities_new
        trip.possible_dates = new_dates
        trip.status = ProposalStatus(int(status))
        db.session.commit()
        flash("Trip edited successfully!")

    return render_template("trips/create_trip.html", trip=trip)

# ---------------------------------------------------------
# TRIP Chat
# ---------------------------------------------------------
@bp.route("/trips/<int:trip_id>/chat", methods=["GET", "POST"])
@login_required
def chat_trip(trip_id):
    trip = TripProposal.query.get_or_404(trip_id)
    if not any(p.user_id == current_user.id for p in trip.participants):
        flash("You are not participating in this trip.")
        return index()
    if request.method == "POST":
        messageText = request.form.get("message")
        message = Message(text=messageText, trip_id=trip_id, user_id=current_user.id)
        db.session.add(message)
        db.session.commit()
    return render_template("trips/message_board.html", messages=trip.messages)
