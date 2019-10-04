# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import logging

from connexion import problem
from flask import current_app, g

from landoapi import auth
from landoapi.repos import get_repos_for_env
from landoapi.storage import db
from landoapi.validation import revision_id_to_int
import enum

logger = logging.getLogger(__name__)

UPLIFT_KEYS = ('user_impact', 'steps_to_reproduce', 'risky', 'string_changes', 'automated_tests', 'nightly', 'risk', 'bug_ids')

@enum.unique
class UpliftRisk(enum.Enum):
    """Risk level of the uplift request."""
    low = "low"
    medium = "medium"
    high = "high"


def validate_uplift_data(data):
    """Validate the data received on the endpoint"""
    logger.info("Validating uplift data {} - {}".format(data, type(data)))
    out = {
        key: data.get(key)
        for key in UPLIFT_KEYS
    }
    logger.info("VALIDATED uplift data {}".format(out))

    # Validate repositories
    out['repositories'] = [
        repo
        for repo in get_repos_for_env(current_app.config.get("ENVIRONMENT"))
        if repo["phid"] in data["repositories"] and repo["approval_required"] is True
    ]
    if not out['repositories']:
        raise ValueError("No valid repositories found")

    return out


@auth.require_auth0(scopes=("lando", "profile", "email"), userinfo=True)
def create(data):
    """Create new uplift requests for requested repositories & revision"""

    revision_id = revision_id_to_int(data["revision_id"])
    try:
        cleaned_data = validate_uplift_data(data)
    except ValueError as e:
        return problem(
            400,
            "Invalid value",
            str(e),
            type="https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/400",
        )
    except Exception as e:
        return problem(
            400,
            'oops',
            str(e),
            type="https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/400",
        )


    for repo in cleaned_data["repositories"]:
        # TODO: check this is not a duplicate

        # TODO: create an uplift request with that patch
        pass

    db.session.commit()

    return {}, 201
