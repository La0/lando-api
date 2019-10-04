# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import logging

from landoapi.phabricator import PhabricatorClient
from landoapi.repos import get_repos_for_env
from landoapi.stacks import (
    build_stack_graph,
    calculate_landable_subgraphs,
    get_landable_repos_for_revision_data,
    request_extended_revision_data,
)

from flask import current_app


logger = logging.getLogger(__name__)


def create_uplift_revision(phab : PhabricatorClient, source_revision_id : int, target_repository : str):
    """
    Create a new revision on a repository, cloning a diff from another repo
    """
    # Check the target repository needs an approval
    repos = get_repos_for_env(current_app.config.get("ENVIRONMENT"))
    local_repo = repos.get(target_repository)
    assert local_repo is not None, f'Unknown repository {target_repository}'
    assert local_repo.approval_required is True, f'No approval required for {target_repository}'

    # Load repo phid from phabricator
    phab_repo = phab.call_conduit(
        "diffusion.repository.search", constraints={"shortNames": [target_repository, ]}
    )
    phab_repo = phab.single(phab_repo, "data")
    logger.info(f"Will create an uplift request on {phab_repo['fields']['name']} - {phab_repo['phid']}")

    from pprint import pprint
    pprint(phab_repo)

    # Find the source diff on phabricator
    source_revision = phab.call_conduit(
        "differential.revision.search", constraints={"ids": [source_revision_id]}
    )
    source_revision = phab.single(source_revision, "data")
    nodes, edges = build_stack_graph(phab, source_revision["phid"])
    print('NODES')
    pprint(nodes)
    print('EDGES')
    pprint(edges)
    stack_data = request_extended_revision_data(phab, [phid for phid in nodes])
    print('Stack')
    pprint(stack_data)


    # Attach it to the new revision just created
    for diff in stack_data.diffs.values():

        # Get raw diff
        raw_diff = phab.call_conduit("differential.getrawdiff", diffID=diff["id"])

        print(raw_diff)

        # Upload it on target repo
        new_diff = phab.call_conduit("differential.createrawdiff", diff=raw_diff, repositoryPHID=phab_repo["phid"])
        new_diff_phid = phab.expect(new_diff, "phid")
        logger.info(f"Created new diff {new_diff_phid}")

        out = phab.call_conduit("differential.revision.edit", transactions=[
            {"type": "update", "value": new_diff_phid},
            {"type": "title", "value": "Uplift request TEST"},
        ])
        pprint(out)

    # Set form (other function ?)
