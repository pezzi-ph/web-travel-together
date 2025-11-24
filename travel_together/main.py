from flask import Blueprint, render_template
from flask_login import login_required, current_user
from model import *

bp = Blueprint("main", __name__, url_prefix="/")


@bp.route("/")
@login_required
def index():
    return render_template("main/index.html", user=current_user)

@bp.route("/landingPage")
@login_required
def landingPage():
    query = db.select(TripProposal)
    .join(TripProposalParticipant)
    .where(TripProposalParticipant.userId == current_user.id)

    trip_proposals = db.session.execute(query).scalars().all()
    return render_template("main/landingPage.html", trip_proposals=trip_proposals)