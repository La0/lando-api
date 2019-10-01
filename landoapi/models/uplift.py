# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
import enum
import logging

from sqlalchemy.dialects.postgresql.json import JSONB
from sqlalchemy.schema import UniqueConstraint

from landoapi.storage import db

logger = logging.getLogger(__name__)


@enum.unique
class UpliftStatus(enum.Enum):
    """Status of the uplift request."""
    created = "created"
    approved = "approved"
    rejected = "rejected"
    landed = "landed"
    failed = "failed"


@enum.unique
class UpliftRisk(enum.Enum):
    """Risk level of the uplift request."""
    low = "low"
    medium = "medium"
    high = "high"


class Uplift(db.Model):
    """Represents an uplift request for a revision."""

    __tablename__ = "uplifts"
    __table_args__ = (
        UniqueConstraint('revision_id', 'repository', name='uplift_revision_repository'),
    )

    # Internal request ID.
    id = db.Column(db.Integer, primary_key=True)

    # Phabricator revision id and repository to land
    # These are unique together
    revision_id = db.Column(db.Integer)
    repository = db.Column(db.String(30))

    # Uplift form data
    user_impact = db.Column(db.Text())
    steps_to_reproduce = db.Column(db.Text())
    risky = db.Column(db.Text())
    bug_ids = db.Column(JSONB, nullable=False)
    string_changes = db.Column(db.Text())
    automated_tests = db.Column(db.Boolean(), nullable=True, default=False)
    nightly = db.Column(db.Boolean(), nullable=False, default=False)
    risk = db.Column(db.Enum(UpliftRisk), nullable=False)

    # LDAP email of the user who requested uplift.
    requester_email = db.Column(db.String(254))

    status = db.Column(
        db.Enum(UpliftStatus), nullable=False, default=UpliftStatus.created
    )
    created_at = db.Column(
        db.DateTime(timezone=True), nullable=False, default=db.func.now()
    )
    updated_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=db.func.now(),
        onupdate=db.func.now(),
    )
