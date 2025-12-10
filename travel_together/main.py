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
from datetime import datetime

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

        # ----- Convert date strings to Python datetime objects -----
        new_dates = []
        for i, departure_str in enumerate(possible_departure_dates):
            # Make sure there is a corresponding return date
            return_str = possible_return_dates[i] if i < len(possible_return_dates) else ""

            # Skip empty rows (in case the user leaves some blank)
            if not departure_str or not return_str:
                continue

            try:
                # HTML datetime-local gives e.g. "2025-12-10T20:35"
                departure_dt = datetime.fromisoformat(departure_str)
                return_dt = datetime.fromisoformat(return_str)
            except ValueError:
                flash("Invalid date format. Please enter valid dates.")
                return redirect(url_for("main.create_trip"))

            if departure_dt > return_dt:
                flash("Departure date cannot be after return date.")
                return redirect(url_for("main.create_trip"))

            new_dates.append(
                PossibleDates(
                    departure_date=departure_dt,
                    return_date=return_dt,
                )
            )

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
def trip_detail(trip_id: int):
    trip = db.session.get(TripProposal, trip_id)
    if trip is None:
        abort(404)

    # Find my participation row, if any
    my_participation = None
    for p in trip.participants:
        if p.user_id == current_user.id:
            my_participation = p
            break

    is_participant = my_participation is not None
    is_editor = bool(my_participation and my_participation.can_edit)

    # Current participant count + "full" flag
    current_count = len(trip.participants)
    is_full = current_count >= trip.max_members

    # Can I join?
    can_join = (
        (not is_participant)
        and (trip.status == ProposalStatus.open)
        and (not is_full)
    )

    # Can I leave?
    can_leave = is_participant
    if can_leave:
        # If trip is still "active" and I'm an editor, I can only leave
        # if there is at least one other editor.
        if trip.status in (
            ProposalStatus.open,
            ProposalStatus.closed_to_new_participants,
        ) and is_editor:
            other_editors = [
                p for p in trip.participants
                if p.user_id != current_user.id and p.can_edit
            ]
            if not other_editors:
                can_leave = False

    return render_template(
        "trips/trip_detail.html",
        trip=trip,
        is_participant=is_participant,
        is_editor=is_editor,
        is_full=is_full,
        can_join=can_join,
        can_leave=can_leave,
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
# LEAVE A TRIP
# ---------------------------------------------------------

@bp.route("/trips/<int:trip_id>/leave", methods=["POST"])
@login_required
def leave_trip(trip_id: int):
    trip = db.session.get(TripProposal, trip_id)
    if trip is None:
        abort(404)

    participation = TripProposalParticipant.query.filter_by(
        trip_id=trip.id,
        user_id=current_user.id,
    ).first()

    if participation is None:
        flash("You are not a participant of this trip.")
        return redirect(url_for("main.trip_detail", trip_id=trip.id))

    # Check the "only editor" rule on active trips
    if trip.status in (
        ProposalStatus.open,
        ProposalStatus.closed_to_new_participants,
    ) and participation.can_edit:
        other_editors = TripProposalParticipant.query.filter(
            TripProposalParticipant.trip_id == trip.id,
            TripProposalParticipant.user_id != current_user.id,
            TripProposalParticipant.can_edit.is_(True),
        ).count()
        if other_editors == 0:
            flash(
                "You are the only editor of this trip. "
                "Give edit rights to another participant before leaving."
            )
            return redirect(url_for("main.trip_detail", trip_id=trip.id))

    db.session.delete(participation)
    db.session.commit()
    flash("You left this trip.")
    return redirect(url_for("main.index"))




# ---------------------------------------------------------
# Edit A TRIP
# ---------------------------------------------------------
@bp.route("/trips/<int:trip_id>/edit", methods=["GET", "POST"])
@login_required
def edit_trip(trip_id):
    # Load trip
    trip = db.session.get(TripProposal, trip_id)
    if trip is None:
        abort(404)

    # Ensure current user is a participant with edit rights
    participation = TripProposalParticipant.query.filter_by(
        trip_id=trip.id,
        user_id=current_user.id,
    ).first()

    if participation is None or not participation.can_edit:
        abort(403)

    if request.method == "POST":
        # ----- BASIC FIELDS -----
        name = request.form.get("name", "").strip()
        departure = request.form.get("departure", "").strip()
        destination = request.form.get("destination", "").strip()
        budget = request.form.get("budget")
        max_members = request.form.get("max_members")
        activities = request.form.getlist("activities[]")
        possible_departure_dates = request.form.getlist("possible_departure_dates[]")
        possible_return_dates = request.form.getlist("possible_return_dates[]")
        status = request.form.get("status")

        # Required fields
        if not name or not departure or not destination:
            flash("Name, departure, and destination are required.")
            return redirect(url_for("main.edit_trip", trip_id=trip.id))

        # ----- LOCATIONS -----
        dep_loc = Location.query.filter_by(name=departure).first()
        if dep_loc is None:
            dep_loc = Location(name=departure)
            db.session.add(dep_loc)

        dest_loc = Location.query.filter_by(name=destination).first()
        if dest_loc is None:
            dest_loc = Location(name=destination)
            db.session.add(dest_loc)

        # ----- ACTIVITIES -----
        new_activities = []
        for text in activities:
            text = text.strip()
            if not text:
                continue        # skip blank rows
            new_activities.append(Activity(name=text))

        # ----- POSSIBLE DATES -----
        new_dates = []
        for i, dep_str in enumerate(possible_departure_dates):
            ret_str = possible_return_dates[i] if i < len(possible_return_dates) else ""

            dep_str = dep_str.strip()
            ret_str = ret_str.strip()
            if not dep_str or not ret_str:
                continue        # skip blank date rows

            try:
                dep_dt = datetime.fromisoformat(dep_str)
                ret_dt = datetime.fromisoformat(ret_str)
            except ValueError:
                flash("Invalid date format. Please enter valid dates.")
                return redirect(url_for("main.edit_trip", trip_id=trip.id))

            if dep_dt > ret_dt:
                flash("Departure date cannot be after return date.")
                return redirect(url_for("main.edit_trip", trip_id=trip.id))

            new_dates.append(
                PossibleDates(
                    departure_date=dep_dt,
                    return_date=ret_dt,
                )
            )

        # ----- UPDATE SCALAR FIELDS -----
        trip.name = name
        trip.departure_location = dep_loc
        trip.destination_location = dest_loc
        trip.budget = int(budget) if budget else 0
        trip.max_members = int(max_members) if max_members else trip.max_members

        if status:
            trip.status = ProposalStatus(int(status))

        # ----- REPLACE CHILD COLLECTIONS -----
        trip.activities.clear()
        trip.activities.extend(new_activities)

        trip.possible_dates.clear()
        trip.possible_dates.extend(new_dates)

        db.session.commit()
        flash("Trip updated successfully.")
        # 👇 after saving, go back to the detail page
        return redirect(url_for("main.trip_detail", trip_id=trip.id))

    # GET: reuse the same form as for create_trip
    return render_template("trips/create_trip.html", trip=trip)

# ---------------------------------------------------------
# TRIP MESSAGE BOARD
# ---------------------------------------------------------
@bp.route("/trips/<int:trip_id>/chat", methods=["GET", "POST"])
@login_required
def message_board(trip_id):
    trip = TripProposal.query.get_or_404(trip_id)

    # Security check: only participants can see/post
    if not any(p.user_id == current_user.id for p in trip.participants):
        flash("You are not participating in this trip.")
        return redirect(url_for("main.index"))

    if request.method == "POST":
        message_text = request.form.get("message", "").strip()
        if message_text:
            message = Message(
                text=message_text,
                trip_id=trip_id,
                user_id=current_user.id,
            )
            db.session.add(message)
            db.session.commit()
            flash("Message posted.")

        return redirect(url_for("main.message_board", trip_id=trip_id))

    # GET: show the board
    return render_template(
        "trips/message_board.html",
        trip=trip,
        messages=trip.messages,
    )

