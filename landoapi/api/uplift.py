# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import logging

from connexion import problem
from flask import current_app, g

from landoapi import auth
from landoapi.repos import get_repos_for_env
from landoapi.validation import revision_id_to_int
from landoapi.uplift import create_uplift_revision
import enum

logger = logging.getLogger(__name__)

UPLIFT_FORM_KEYS = ('user_impact', 'steps_to_reproduce', 'risky', 'string_changes', 'automated_tests', 'nightly', 'risk', 'bug_ids')

@enum.unique
class UpliftRisk(enum.Enum):
    """Risk level of the uplift request."""
    low = "low"
    medium = "medium"
    high = "high"


def validate_uplift_data(data):
    """Validate the data received on the endpoint"""
    form_data = {
        key: data.get(key)
        for key in UPLIFT_FORM_KEYS
    }

    # Validate repositories
    repositories = [
        repo_key
        for repo_key, repo in get_repos_for_env(current_app.config.get("ENVIRONMENT")).items()
        if repo_key in data["repositories"] and repo["approval_required"] is True
    ]
    if not repositories:
        raise ValueError("No valid repositories found")

    return form_data, repositories


@auth.require_auth0(scopes=("lando", "profile", "email"), userinfo=True)
def create(data):
    """Create new uplift requests for requested repositories & revision"""

    revision_id = revision_id_to_int(data["revision_id"])
    try:
        cleaned_data, repositories = validate_uplift_data(data)
    except ValueError as e:
        return problem(
            400,
            "Invalid value",
            str(e),
            type="https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/400",
        )

    for repo in repositories:
        # TODO: check this is not a duplicate

        create_uplift_revision(g.phabricator, revision_id, repo, cleaned_data)

    return {}, 201
