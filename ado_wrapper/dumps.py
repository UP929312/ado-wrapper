"""This file hosts a collection of dumps with the purpose of documenting the responses, all personal information has been removed."""

# flake8: noqa
# fmt: off

ADO_USER_DUMP = {
    "subjectKind": "user",
    "metaType": "member",
    "directoryAlias": "<first.last>",
    "domain": "<32_char_uuid>",
    "principalName": "<first.last@company.com>",
    "mailAddress": "<first.last@company.com>",
    "origin": "aad",
    "originId": "<32_char_uuid>",
    "displayName": "<First> <Last>",
    "_links": {"self": {"href": "https://vssps.dev.azure.com/{ado_client.org}/_apis/Graph/Users/<user_descriptor>"}, "memberships": {"href": "https://vssps.dev.azure.com/{ado_client.org}/_apis/Graph/Memberships/<user_descriptor>"}, "membershipState": {"href": "https://vssps.dev.azure.com/{ado_client.org}/_apis/Graph/MembershipStates/<user_descriptor>"}, "storageKey": {"href": "https://vssps.dev.azure.com/{ado_client.org}/_apis/Graph/StorageKeys/<user_descriptor>"}, "avatar": {"href": "https://dev.azure.com/{ado_client.org}/_apis/GraphProfile/MemberAvatars/<user_descriptor>"}},
    "url": "https://vssps.dev.azure.com/{ado_client.org}/_apis/Graph/Users/<user_descriptor>",
    "descriptor": "<user_descriptor>",
}

ARTIFACT_DUMP = [
    {
        'id': "{artifact_id}",
        'name': '{artifact_name}',
        'source': '{source_job_id_uuid}',  # The artifact source, which will be the ID of the job that produced this artifact. If an artifact is associated with multiple sources, this points to the first source.
        'resource': {
            'type': 'Container',
            'data': '#/71951719/{artifact_name}',
            'properties': {
                'localpath': '/home/vsts/work/1/s/{path_data}', 
                'artifactsize': '12025'
            },
            'url': 'https://dev.azure.com/{ado_client.ado_org_name}/{ado_client.ado_project_id}/_apis/build/builds/{build_id}/artifacts?artifactName={artifact_name}&api-version=7.1-preview.5',
            'downloadUrl': 'https://dev.azure.com/{ado_client.ado_org_name}/{ado_client.ado_project_id}/_apis/build/builds/{build_id}/artifacts?artifactName={artifact_name}-1&api-version=7.1-preview.5&%24format=zip'
        }
    },
    # <another copy>
]

AUDIT_LOG_DUMP = {
    'id': '999999999999999999;00000000-0000-0000-0000-000000000000;00000000-0000-0000-0000-000000000000',
    'correlationId': '00000000-0000-0000-0000-000000000000',
    'activityId': '00000000-0000-0000-0000-000000000000',
    'actorCUID': '00000000-0000-0000-0000-000000000000',
    'actorUserId': '00000000-0000-0000-0000-000000000000',  # Same as above
    'actorClientId': '00000000-0000-0000-0000-000000000000',
    'actorUPN': 'first.last@example.com',
    'authenticationMechanism': 'PAT_Unscoped authorizationId:<32_char_uuid>',
    'timestamp': '2024-01-01T01:01:01.01Z',
    'scopeType': 'organization',
    'scopeDisplayName': '<org_name> (Organization)',
    'scopeId': '00000000-0000-0000-0000-000000000000',
    'projectId': '00000000-0000-0000-0000-000000000000',
    'projectName': None,
    'ipAddress': '128.128.128.128',
    'userAgent': 'VSServices/128.128.123456.0 (NetStandard; Linux 5.10.215-203.850.amzn2.x86_64 #1 SMP Tue Apr 23 20:32:19 UTC 2024) VstsAgentCore-l',
    'actionId': 'Library.AgentAdded',
    'data': {...},
    'details': 'Added agent <agent_name> to pool <pool_name>.',
    'area': 'Library',
    'category': 'modify',
    'categoryDisplayName': 'Modify',
    'actorDisplayName': 'First Last',
    'actorImageUrl': 'https://dev.azure.com/vfuk-digital/_apis/GraphProfile/MemberAvatars/<User Descriptor>'
}


BRANCH_DUMP = {
    "name": "refs/heads/test-branch",
    "objectId": "<object_id>",
    "creator": {"displayName": "<First> <Last>", "url": "https://spsprodweu5.vssps.visualstudio.com/<some_id>/_apis/Identities/<user_id>", "_links": {"avatar": {"href": "https://dev.azure.com/{ado_client.org}/_apis/GraphProfile/MemberAvatars/<user_descriptor>"}}, "id": "<user_id>", "uniqueName": "<first.last@company.com>", "imageUrl": "https://dev.azure.com/{ado_client.org}/_api/_common/identityImage?id=<user_id>", "descriptor": "<user_descriptor>"},
    "url": "https://dev.azure.com/{ado_client.org}/{ado_client.project_id}/_apis/git/repositories/<repo_id>/refs?filter=heads%2Ftest-branch",
}

BRANCH_CREATE_DUMP = {
    'value': [
        {
            'repositoryId': 'eb1db59a-325a-4111-b2c4-09c9f74e02ed',
            'name': 'refs/heads/test-branch',
            'oldObjectId': '0000000000000000000000000000000000000000',
            'newObjectId': '3277815d22bebee867474ea4ab0fb8a500c82b21',
            'isLocked': False,
            'updateStatus':
            'succeeded',
            'success': True
        }
    ],
    'count': 1
}

BUILD_DUMP = {
    "_links": {"self": {"href": "https://dev.azure.com/{ado_client.org}/{ado_client.project_id}/_apis/build/Builds/93458"}, "web": {"href": "https://dev.azure.com/{ado_client.org}/{ado_client.project_id}/_build/results?buildId=93458"}, "sourceVersionDisplayUri": {"href": "https://dev.azure.com/{ado_client.org}/{ado_client.project_id}/_apis/build/builds/{build_id}/sources"}, "timeline": {"href": "https://dev.azure.com/{ado_client.org}/{ado_client.project_id}/_apis/build/builds/{build_id}/Timeline"}, "badge": {"href": "https://dev.azure.com/{ado_client.org}/{ado_client.project_id}/_apis/build/status/{build_def_id}"}},
    "properties": {},
    "tags": [],
    "validationResults": [],
    "plans": [
        {"planId": "<32_char_id>"}
    ],
    "triggerInfo": {},
    "id": "{build_id}",
    "buildNumber": "20240101.1",
    "status": "notStarted",
    "queueTime": "2024-03-17T11:03:29.2982876Z",
    "url": "https://dev.azure.com/{ado_client.org}/{ado_client.project_id}/_apis/build/Builds/{build_id}",
    "definition": {"drafts": [], "id": "{build_def_id}", "name": "ado_wrapper-test-build", "url": "https://dev.azure.com/{ado_client.org}/{ado_client.project_id}/_apis/build/Definitions/{build_id}?revision=1", "uri": "vstfs:///Build/Definition/{build_id}", "path": "\\", "type": "build", "queueStatus": "enabled", "revision": 1, "project": {"id": "{ado_client.project_id}", "name": "{ado_client.project}", "url": "https://dev.azure.com/{ado_client.org}/_apis/projects/{ado_client.project_id}", "state": "wellFormed", "revision": "{revision}", "visibility": "private", "lastUpdateTime": "2024-01-01T12:14:30.36Z"}},
    "buildNumberRevision": 1,
    "project": {"id": "{ado_client.project_id}", "name": "{ado_client.project}", "url": "https://dev.azure.com/{ado_client.org}/_apis/projects/{ado_client.project_id}", "state": "wellFormed", "revision": 399, "visibility": "private", "lastUpdateTime": "2024-02-06T14:14:30.36Z"},
    "uri": "vstfs:///Build/Build/93458",
    "sourceBranch": "refs/heads/my-branch",
    "sourceVersion": "<commit_id>",
    "queue": {"id": "{queue_id}", "name": "<pool_name>", "pool": {"id": "{pool_id}", "name": "<pool_name"}},
    "priority": "normal",
    "reason": "manual",
    "requestedFor": {"displayName": "<First Last>", "url": "https://spsprodweu5.vssps.visualstudio.com/<some_id>/_apis/Identities/<user_id>", "_links": {"avatar": {"href": "https://dev.azure.com/{ado_client.org}/_apis/GraphProfile/MemberAvatars/<user_descriptor>"}}, "id": "<user_id>", "uniqueName": "<first.last@company.com>", "imageUrl": "https://dev.azure.com/{ado_client.org}/_apis/GraphProfile/MemberAvatars/<user_descriptor>", "descriptor": "<user_descriptor>"},
    "requestedBy": {"displayName": "<First Last>", "url": "https://spsprodweu5.vssps.visualstudio.com/<some_id>/_apis/Identities/<user_id>", "_links": {"avatar": {"href": "https://dev.azure.com/{ado_client.org}/_apis/GraphProfile/MemberAvatars/<user_descriptor>"}}, "id": "<user_id>", "uniqueName": "<first.last@company.com>", "imageUrl": "https://dev.azure.com/{ado_client.org}/_apis/GraphProfile/MemberAvatars/<user_descriptor>", "descriptor": "<user_descriptor>"},
    "lastChangedDate": "2024-03-17T11:03:29.373Z",
    "lastChangedBy": {"displayName": "<First Last>", "url": "https://spsprodweu5.vssps.visualstudio.com/<some_id>/_apis/Identities/<user_id>", "_links": {"avatar": {"href": "https://dev.azure.com/{ado_client.org}/_apis/GraphProfile/MemberAvatars/<user_descriptor>"}}, "id": "<user_id>", "uniqueName": "<first.last@company.com>", "imageUrl": "https://dev.azure.com/{ado_client.org}/_apis/GraphProfile/MemberAvatars/<user_descriptor>", "descriptor": "<user_descriptor>"},
    "orchestrationPlan": {"planId": "<plan_id>"},
    "logs": {"id": 0, "type": "Container", "url": "https://dev.azure.com/{ado_client.org}/{ado_client.project_id}/_apis/build/builds/93458/logs"},
    "repository": {"id": "<repo_id>", "type": "TfsGit", "name": "ado_wrapper-test-repo-for-create-delete-builds", "url": "https://dev.azure.com/{ado_client.org}/{ado_client.project}/_git/ado_wrapper-test-repo-for-create-delete-builds", "clean": None, "checkoutSubmodules": False},
    "retainedByRelease": False,
    "triggeredByBuild": None,
    "appendCommitMessageToRunName": True
}

BUILD_DEFINITION_DUMP = {
    "properties": {},
    "tags": [],
    "_links": {"self": {"href": "https://dev.azure.com/{ado_client.org}/{ado_client.project_id}/_apis/build/Definitions/2601?revision=1"}, "web": {"href": "https://dev.azure.com/{ado_client.org}/{ado_client.project_id}/_build/definition?definitionId=2601"}, "editor": {"href": "https://dev.azure.com/{ado_client.org}/{ado_client.project_id}/_build/designer?id=2601&_a=edit-build-definition"}, "badge": {"href": "https://dev.azure.com/{ado_client.org}/{ado_client.project_id}/_apis/build/status/2601"}},
    "description": "<description>",
    "jobAuthorizationScope": "projectCollection",
    "process": {"yamlFilename": "build.yaml", "type": 2},
    "repository": {"id": "<repo_id>", "type": "TfsGit", "name": "ado_wrapper-test-repo-for-create-delete-builds", "url": "https://dev.azure.com/{ado_client.org}/{ado_client.project}/_git/ado_wrapper-test-repo-for-create-delete-builds", "defaultBranch": "refs/heads/my-branch", "clean": None, "checkoutSubmodules": False},
    "quality": "definition",
    "authoredBy": {"displayName": "<First> <Last>", "url": "https://spsprodweu5.vssps.visualstudio.com/<some_id>/_apis/Identities/<user_id>", "_links": {"avatar": {"href": "https://dev.azure.com/{ado_client.org}/_apis/GraphProfile/MemberAvatars/<user_descriptor>"}}, "id": "<user_id>", "uniqueName": "<first.last@company.com>", "imageUrl": "https://dev.azure.com/{ado_client.org}/_apis/GraphProfile/MemberAvatars/<user_descriptor>", "descriptor": "<user_descriptor>"},
    "drafts": [],
    "queue": {"_links": {"self": {"href": "https://dev.azure.com/{ado_client.org}/_apis/build/Queues/575"}}, "id": 575, "name": "<pool_name>", "url": "https://dev.azure.com/{ado_client.org}/_apis/build/Queues/575", "pool": {"id": 195, "name": "<pool_name>"}},
    "id": 2601,
    "name": "ado_wrapper-test-build",
    "url": "https://dev.azure.com/{ado_client.org}/{ado_client.project_id}/_apis/build/Definitions/2601?revision=1",
    "uri": "vstfs:///Build/Definition/2601",
    "path": "\\",
    "type": "build",
    "queueStatus": "enabled",
    "revision": 1,
    "createdDate": "2024-03-17T11:03:28.943Z",
    "project": {"id": "{ado_client.project_id}", "name": "{ado_client.project}", "url": "https://dev.azure.com/{ado_client.org}/_apis/projects/{ado_client.project_id}", "state": "wellFormed", "revision": 399, "visibility": "private", "lastUpdateTime": "2024-02-06T14:14:30.36Z"}
}

BUILD_DEFINITION_HIERARCHY_CREATE_DUMP = {
    'dataProviderSharedData': {},
    'dataProviders': {
        'ms.vss-web.component-data': {},
        'ms.vss-web.shared-data': None,
        'ms.vss-build-web.create-and-run-pipeline-data-provider': {
            'pipeline': {'id': '<build_def_id>', 'name': '<build_def_name>', 'queueName': 'Azure Pipelines'}
        }
    }
}

COMMIT_DUMP = {
    "commitId": "<commit_id>",
    "author": {"name": "<First Last>", "email": "<first.last@company.com>", "date": "2024-03-17T11:45:19Z"},
    "committer": {"name": "<First Last>", "email": "<first.last@company.com>", "date": "2024-03-17T11:45:19Z"},
    "comment": "Add README.md",
    "changeCounts": {"Add": 1, "Edit": 0, "Delete": 0},
    "url": "https://dev.azure.com/{ado_client.org}/{ado_client.project_id}/_apis/git/repositories/<repo_id>/commits/<commit_id>",
    "remoteUrl": "https://dev.azure.com/{ado_client.org}/{ado_client.project}/_git/ado_wrapper-test-repo-for-create-delete-builds/commit/<other_commit_id>",
}

GROUP_DUMP = {
    "subjectKind": "group",
    "description": "{description}",
    "domain": "vstfs:///Classification/TeamProject/{group_id}",
    "principalName": "Our Team Name",
    "mailAddress": None,
    "origin": "vsts",
    "originId": "{originId}",
    "displayName": "Our Team",
    "_links": {"self": {"href": "https://vssps.dev.azure.com/{ado_client.org}/_apis/Graph/Groups/{subject_descriptor}"}, "memberships": {"href": "https://vssps.dev.azure.com/{ado_client.org}/_apis/Graph/Memberships/{subject_descriptor}"}, "membershipState": {"href": "https://vssps.dev.azure.com/{ado_client.org}/_apis/Graph/MembershipStates/{subject_descriptor}"}, "storageKey": {"href": "https://vssps.dev.azure.com/{ado_client.org}/_apis/Graph/StorageKeys/{subject_descriptor}"}},
    "url": "https://vssps.dev.azure.com/{ado_client.org}/_apis/Graph/Groups/{subject_descriptor}"
}

PERMISSIONS_DUMP = [
    {'securityNamespaceId': '2e9eb7ed-3c0a-47d4-87c1-0ffdd275fd87', 'token': 'repoV2/{ado_client.ado_project_id}', 'permissions': 256, 'value': True}, {'securityNamespaceId': '49b48001-ca20-4adc-8111-5b60c903a50c', 'token': 'repoV2/{ado_client.ado_project_id}', 'permissions': 256, 'value': False}
]

PROJECT_DUMP = {
    "id": "<32_char_uuid>",
    "name": "<project_name>",
    "description": "<description>",
    "url": "https://dev.azure.com/{ado_client.org}/_apis/projects/<project_id>",
    "state": "wellFormed",
    "revision": 194,
    "visibility": "private",
    "lastUpdateTime": "2024-03-18T16:41:05.14Z",
}

PULL_REQUEST_DUMP = {
    "repository ": {"id": "<repo_id>", "name": "ado_wrapper-test-repo-for-get-pull-request-by-id", "url": "https://dev.azure.com/{ado_client.org}/{ado_client.project_id}/_apis/git/repositories/<repo_id>", "project": {"id": "<project_id>", "name": "<project_name>", "url": "https://dev.azure.com/{ado_client.org}/_apis/projects/{ado_client.project_id}", "state": "wellFormed", "revision": 399, "visibility": "private", "lastUpdateTime": "2024-02-06T14:14:30.36Z"}, "size": 980, "remoteUrl": "https://{ado_client.org}@dev.azure.com/{ado_client.org}/{ado_client.project}/_git/ado_wrapper-test-repo-for-get-pull-request-by-id", "sshUrl": "git@ssh.dev.azure.com:v3/{ado_client.org}/{ado_client.project}/ado_wrapper-test-repo-for-get-pull-request-by-id", "webUrl": "https://dev.azure.com/{ado_client.org}/{ado_client.project}/_git/ado_wrapper-test-repo-for-get-pull-request-by-id", "isDisabled": False, "isInMaintenance": False},
    "pullRequestId": "{pull_request_id}",
    "codeReviewId": "{code_review_id}",
    "status": "active",
    "createdBy": {"displayName": "<First Last>", "url": "https://spsprodweu5.vssps.visualstudio.com/<some_id>/_apis/Identities/<user_id>", "_links": {"avatar": {"href": "https://dev.azure.com/{ado_client.org}/_apis/GraphProfile/MemberAvatars/<user_descriptor>"}}, "id": "<user_id>", "uniqueName": "<first.last@company.com>", "imageUrl": "https://dev.azure.com/{ado_client.org}/_api/_common/identityImage?id=<user_id>", "descriptor": "<user_descriptor>"},
    "creationDate": "2021-03-17T11:18:39.9163346Z",
    "title": "<title>",
    "description": "<description>",
    "sourceRefName": "refs/heads/test-branch",
    "targetRefName": "refs/heads/main",
    "mergeStatus": "succeeded",
    "isDraft": False,
    "mergeId": "<32_char_uuid>",
    "lastMergeSourceCommit": {"commitId": "<commit_id>", "url": "https://dev.azure.com/{ado_client.org}/{ado_client.project_id}/_apis/git/repositories/<repo_id>/commits/<commit_id>"},
    "lastMergeTargetCommit": {"commitId": "<commit_id>", "url": "https://dev.azure.com/{ado_client.org}/{ado_client.project_id}/_apis/git/repositories/<repo_id>/commits/<commit_id>"},
    "lastMergeCommit": {"commitId": "<commit_id>", "author": {"name": "<First Last>", "email": "<first.last@company.com>", "date": "2024-03-17T11:18:40Z"}, "committer": {"name": "<First Last>", "email": "<first.last@company.com>", "date": "2024-03-17T11:18:40Z"}, "comment": "<comment>", "url": "https://dev.azure.com/{ado_client.org}/{ado_client.project_id}/_apis/git/repositories/<repo_id>/commits/<commit_id>"},
    "reviewers": [],
    "url": "https://dev.azure.com/{ado_client.org}/{ado_client.project_id}/_apis/git/repositories/<repo_id>/pullRequests/10237",
    "_links": {"self": {"href": "https://dev.azure.com/{ado_client.org}/{ado_client.project_id}/_apis/git/repositories/<repo_id>/pullRequests/10237"}, "repository": {"href": "https://dev.azure.com/{ado_client.org}/{ado_client.project_id}/_apis/git/repositories/<repo_id>"}, "workItems": {"href": "https://dev.azure.com/{ado_client.org}/{ado_client.project_id}/_apis/git/repositories/<repo_id>/pullRequests/10237/workitems"}, "sourceBranch": {"href": "https://dev.azure.com/{ado_client.org}/{ado_client.project_id}/_apis/git/repositories/<repo_id>/refs/heads/test-branch"}, "targetBranch": {"href": "https://dev.azure.com/{ado_client.org}/{ado_client.project_id}/_apis/git/repositories/<repo_id>/refs/heads/main"}, "statuses": {"href": "https://dev.azure.com/{ado_client.org}/{ado_client.project_id}/_apis/git/repositories/<repo_id>/pullRequests/10237/statuses"}, "sourceCommit": {"href": "https://dev.azure.com/{ado_client.org}/{ado_client.project_id}/_apis/git/repositories/<repo_id>/commits/<commit_id>"}, "targetCommit": {"href": "https://dev.azure.com/{ado_client.org}/{ado_client.project_id}/_apis/git/repositories/<repo_id>/commits/<commit_id>"}, "createdBy": {"href": "https://spsprodweu5.vssps.visualstudio.com/<some_id>/_apis/Identities/<user_id>"}, "iterations": {"href": "https://dev.azure.com/{ado_client.org}/{ado_client.project_id}/_apis/git/repositories/<repo_id>/pullRequests/10237/iterations"}},
    "supportsIterations": True,
    "artifactId": "vstfs:///Git/PullRequestId/<project_id>%2f<repo_id>%2f10237"
}

PULL_REQUEST_SET_ASSIGNED_TO_MY_TEAM = {
    "pullRequestListCustomCriteria":
        [
            {"authorIds": ["<author_id>"], "groupByVote": False, "id": "CreatedByMe", "includeDuplicates": False, "readonly": True, "status": 1, "title": "Created by me"},
            {"groupByVote": True, "id": "AssignedToMe", "includeDuplicates": False, "readonly": True, "reviewerIds": ["<author_id>"], "status": 1, "title": "Assigned to me"},
            {"authorIds": [], "id": "AssignedToMyTeams", "myTeamsAsReviewer": True, "status": 2, "title": "Assigned to my teams"}
        ]
}

REPO_DUMP = {
    "id": "<repo_id>",
    "name": "{repo_name}",
    "url": "https://dev.azure.com/{ado_client.org}/{ado_client.project_id}/_apis/git/repositories/{self.repo_id}",
    "project": {"id": "{ado_client.project_id}", "name": "{<project_name>}", "url": "https://dev.azure.com/{ado_client.org}/_apis/projects/{ado_client.project_id}", "state": "wellFormed", "revision": 399, "visibility": "private", "lastUpdateTime": "2024-02-06T14:14:30.36Z"},
    "size": 0,
    "remoteUrl": "https://{ado_client.org}@dev.azure.com/{ado_client.org}/{ado_client.project}/_git/{repo_name}",
    "sshUrl": "git@ssh.dev.azure.com:v3/{ado_client.org}/{ado_client.project}/{repo_name}",
    "webUrl": "https://dev.azure.com/{ado_client.org}/{ado_client.project}/_git/{repo_name}",
    "isDisabled": False,
    "isInMaintenance": False,
}

REPO_POLICY_DUMP = {
    'dataProviderSharedData': {},
    'dataProviders': {
        'ms.vss-web.component-data': {}, 'ms.vss-web.shared-data': None, 'ms.vss-code-web.branch-policies-data-provider': {
            'identities': "<Member>", 'supportServicePrincipals': True, 'isEditable': True, 'buildDefinitions': None, 'recentStatuses': None,
            'policyGroups': {'{policy_id_uuid}': {
                             'currentScopePolicies': [{'createdBy': "<Member>", 'createdDate': '/Date(1712832031819)/',
                                                       'isEnabled': True, 'isBlocking': True, 'isDeleted': False, 'settings': {'minimumApproverCount': 1, 'creatorVoteCounts': False, 'allowDownvotes': False, 'resetOnSourcePush': False, 'requireVoteOnLastIteration': False, 'resetRejectionsOnSourcePush': False, 'blockLastPusherVote': True, 'requireVoteOnEachIteration': False, 'scope': [{'refName': 'refs/heads/main', 'matchKind': 'Exact', 'repositoryId': '{repo_id}'}]}, 'isEnterpriseManaged': False, '_links': "<links>", 'revision': 13, 'id': 8178, 'url': 'https://dev.azure.com/{ado_org_name}/{repo_id}/_apis/policy/configurations/8178', 'type': {'id': '{policy_id_uuid}', 'url': 'https://dev.azure.com/{ado_org_name}/{repo_id}/_apis/policy/types/{policy_id_uuid}', 'displayName': 'Minimum number of reviewers'}}], 'enterpriseManagedPolicies': None,
                                                       'inheritedPolicies': [{'createdBy': "<Member>", 'createdDate': '/Date(1710074353140)/', 'isEnabled': True, 'isBlocking': True, 'isDeleted': False, 'settings': {'minimumApproverCount': 1, 'creatorVoteCounts': False, 'allowDownvotes': False, 'resetOnSourcePush': False, 'requireVoteOnLastIteration': False, 'resetRejectionsOnSourcePush': False, 'blockLastPusherVote': False, 'requireVoteOnEachIteration': False, 'scope': [{'refName': None, 'matchKind': 'DefaultBranch', 'repositoryId': None}]}, 'isEnterpriseManaged': False, '_links': {'self': {'href': 'https://dev.azure.com/{ado_org_name}/{repo_id}/_apis/policy/configurations/{config_id}'}, 'policyType': {'href': 'https://dev.azure.com/{ado_org_name}/{repo_id}/_apis/policy/types/{policy_id_uuid}'}}, 'revision': 2, 'id': "{config_id}", 'url': 'https://dev.azure.com/{ado_org_name}/{repo_id}/_apis/policy/configurations/{config_id}', 'type': {'id': '{policy_id_uuid}', 'url': 'https://dev.azure.com/{ado_org_name}/{repo_id}/_apis/policy/types/{policy_id_uuid}', 'displayName': 'Minimum number of reviewers'}}]}, 'c6a1889d-b943-4856-b76f-9e46bb6b0df2': {'currentScopePolicies': None, 'enterpriseManagedPolicies': None,
                                                        'inheritedPolicies': [{'createdBy': "<Member>", 'createdDate': '/Date(1670239096642)/', 'isEnabled': True, 'isBlocking': True, 'isDeleted': False, 'settings': {'scope': [{'refName': None, 'matchKind': 'DefaultBranch', 'repositoryId': None}]}, 'isEnterpriseManaged': False, '_links': {'self': {'href': 'https://dev.azure.com/{ado_org_name}/{repo_id}/_apis/policy/configurations/40'}, 'policyType': {'href': 'https://dev.azure.com/{ado_org_name}/{repo_id}/_apis/policy/types/c6a1889d-b943-4856-b76f-9e46bb6b0df2'}}, 'revision': 1, 'id': 40, 'url': 'https://dev.azure.com/{ado_org_name}/{repo_id}/_apis/policy/configurations/40', 'type': {'id': 'c6a1889d-b943-4856-b76f-9e46bb6b0df2', 'url': 'https://dev.azure.com/{ado_org_name}/{repo_id}/_apis/policy/types/c6a1889d-b943-4856-b76f-9e46bb6b0df2', 'displayName': 'Comment requirements'}}]},
                                                        'fd2167ab-b0be-447a-8ec8-39368250530e': {'currentScopePolicies': [{'createdBy': "<Member>", 'createdDate': '/Date(1712766957032)/', 'isEnabled': True, 'isBlocking': True, 'isDeleted': False, 'settings': {'requiredReviewerIds': ['ab35e0e5-b36d-46c4-8d91-714d413e4fae'], 'minimumApproverCount': 1, 'creatorVoteCounts': True, 'scope': [{'refName': 'refs/heads/main', 'matchKind': 'Exact', 'repositoryId': '1aa43e9c-ffca-4388-98b5-59b272a497b8'}]}, 'isEnterpriseManaged': False, '_links': {'self': {'href': 'https://dev.azure.com/{ado_org_name}/{repo_id}/_apis/policy/configurations/8179'}, 'policyType': {'href': 'https://dev.azure.com/{ado_org_name}/{repo_id}/_apis/policy/types/fd2167ab-b0be-447a-8ec8-39368250530e'}}, 'revision': 1, 'id': 8179, 'url': 'https://dev.azure.com/{ado_org_name}/{repo_id}/_apis/policy/configurations/8179', 'type': {'id': 'fd2167ab-b0be-447a-8ec8-39368250530e', 'url': 'https://dev.azure.com/{ado_org_name}/{repo_id}/_apis/policy/types/fd2167ab-b0be-447a-8ec8-39368250530e', 'displayName': 'Required reviewers'}}],
                                                                                                'enterpriseManagedPolicies': None, 'inheritedPolicies': None}},
        }},
}

RUN_DUMP = {
    '_links': {'self': {'href': 'https://dev.azure.com/{ado_client.org}/{ado_client.project_id}/_apis/pipelines/<pipeline_id>/runs/<run_id>'}, 'web': {'href': 'https://dev.azure.com/{ado_client.org}/{ado_client.project_id}/_build/results?buildId=<run_id>'}, 'pipeline.web': {'href': 'https://dev.azure.com/{ado_client.org}/{ado_client.project_id}/_build/definition?definitionId=<pipeline_id>'}, 'pipeline': {'href': 'https://dev.azure.com/{ado_client.org}/{ado_client.project_id}/_apis/pipelines/<pipeline_id>?revision=1'}},
    'templateParameters': {},
    'pipeline': {'url': 'https://dev.azure.com/{ado_client.org}/{ado_client.project_id}/_apis/pipelines/<pipeline_id>?revision=1', 'id': "<pipeline_id>", 'revision': 1, 'name': 'ado_wrapper-test-run-for-create-delete-run', 'folder': '\\'},
    'state': 'inProgress',
    'createdDate': '2024-06-09T11:09:37.6538446Z',
    'url': 'https://dev.azure.com/{ado_client.org}/{ado_client.project_id}/_apis/pipelines/<pipeline_id>/runs/<run_id>',
    'resources': {'repositories': {'self': {'repository': {'id': '<repo_id>', 'type': 'azureReposGit'}, 'refName': 'refs/heads/my-branch', 'version': 'bf9b3ae18fa2bd5c0f6c99f7ad67f5e58e0a6a8e'}}},
    'id': "<run_id>",
    'name': '20240609.1',
}

RUN_RESULT_DUMP = {
    "id": "a8c942cb-b48a-5d20-399e-e9c5aed77b37",
    "name": "Build",
    "imageName": "Ubuntu-20.04",
    "queueId": 36,
    "stageName": "stage name with spaces",
    "stageId": "<32char_uuid>",
    "startTime": "/Date(1720168453910)/",
    "finishTime": "/Date(1720168463150)/",
    "stateData": {
        "pendingDependencies": False,
        "pendingChecks": False,
    },
    "linkProps": {
        "href": "/{ado_org_name}/{ado_project_id}}/_build/results?buildId={build_id}&view=logs&j=a8c942cb-b48a-5d20-399e-e9c5aed77b37"
    },
    "state": 2,
    "result": 0
}

SERVICE_ENDPOINT_DUMP = {
    "data": {},
    "id": "{service_endpoint_id}",
    "name": "{service_connection_name}",
    "type": "github",
    "url": "https://github.com",
    "createdBy": "<Member>",
    "description": "{description}",
    "authorization": {"parameters": {"AccessToken": None}, "scheme": "Token"},
    "isShared": False,
    "isOutdated": False, "isReady": True,
    "owner": "Library",
    "serviceEndpointProjectReferences": [{"projectReference": {"id": "{project_id}", "name": "{project_name}"},
                                          "name": "{service_connection_name}", "description": "{description}"}]
}

TEAM_DUMP = {
    "id": "<32_char_uuid>",
    "name": "Systems Team",
    "url": "https://dev.azure.com/{ado_client.org}/_apis/projects/{ado_client.project_id}/teams/<32_char_uuid>",
    "description": "<description>",
    "identityUrl": "https://spsprodweu5.vssps.visualstudio.com/<some_id>/_apis/Identities/<32_char_uuid>",
    "projectName": "<project_name",
    "projectId": "<32_char_uuid>"
}

VARIABLE_GROUP_DUMP = {
    "variables": {"a": {"value": "b", "isReadOnly": True}},
    "id": 528,
    "type": "Vsts",
    "name": "ado_wrapper-test-for-create-delete",
    "description": "my_description",
    "createdBy": {"displayName": None, "id": "<user_id>"},
    "createdOn": "2024-03-17T11:04:25.4233333Z",
    "modifiedBy": {"displayName": None, "id": "<user_id>"},
    "modifiedOn": "2024-03-17T11:04:25.4233333Z",
    "isShared": False,
    "variableGroupProjectReferences": [
        {"projectReference": {"id": "{ado_client.project_id}", "name": "<project_name"}, "name": "{repo_name}", "description": "{description}"}
    ]
}

URL_FOR_YAML_VALIDATOR = "https://dev.azure.com/{ado_client.ado_org_name}/{ado_client.ado_project_name}/_apps/hub/ms.vss-build-web.ci-designer-hub?pipelineId={definition_id}"

# fmt: on
