"""This file hosts a collection of dumps with the purpose of documenting the responses, all personal information has been removed."""

ADO_USER_DUMP = {
    'subjectKind': 'user',
    'metaType': 'member',
    'directoryAlias': '<first.last>',
    'domain': '<32_char_uuid>',
    'principalName': '<first.last@company.com>',
    'mailAddress': '<first.last@company.com>',
    'origin': 'aad',
    'originId': '<32_char_uuid>',
    'displayName': '<First> <Last>',
    '_links': {'self': {'href': 'https://vssps.dev.azure.com/{ado_client.org}/_apis/Graph/Users/<user_descriptor>'}, 'memberships': {'href': 'https://vssps.dev.azure.com/{ado_client.org}/_apis/Graph/Memberships/<user_descriptor>'}, 'membershipState': {'href': 'https://vssps.dev.azure.com/{ado_client.org}/_apis/Graph/MembershipStates/<user_descriptor>'}, 'storageKey': {'href': 'https://vssps.dev.azure.com/{ado_client.org}/_apis/Graph/StorageKeys/<user_descriptor>'}, 'avatar': {'href': 'https://dev.azure.com/{ado_client.org}/_apis/GraphProfile/MemberAvatars/<user_descriptor>'}},
    'url': 'https://vssps.dev.azure.com/{ado_client.org}/_apis/Graph/Users/<user_descriptor>',
    'descriptor': '<user_descriptor>',
}

BRANCH_DUMP = {
    'name': 'refs/heads/test-branch',
    'objectId': '<object_id>',
    'creator': {'displayName': '<First> <Last>', 'url': 'https://spsprodweu5.vssps.visualstudio.com/<some_id>/_apis/Identities/<user_id>', '_links': {'avatar': {'href': 'https://dev.azure.com/{ado_client.org}/_apis/GraphProfile/MemberAvatars/<user_descriptor>'}}, 'id': '<user_id>', 'uniqueName': '<first.last@company.com>', 'imageUrl': 'https://dev.azure.com/{ado_client.org}/_api/_common/identityImage?id=<user_id>', 'descriptor': '<user_descriptor>'},
    'url': 'https://dev.azure.com/{ado_client.org}/{ado_client.project_id}/_apis/git/repositories/<repo_id>/refs?filter=heads%2Ftest-branch',
}

BUILD_DUMP = {
    '_links': {'self': {'href': 'https://dev.azure.com/{ado_client.org}/{ado_client.project_id}/_apis/build/Builds/93458'}, 'web': {'href': 'https://dev.azure.com/{ado_client.org}/{ado_client.project_id}/_build/results?buildId=93458'}, 'sourceVersionDisplayUri': {'href': 'https://dev.azure.com/{ado_client.org}/{ado_client.project_id}/_apis/build/builds/{build_id}/sources'}, 'timeline': {'href': 'https://dev.azure.com/{ado_client.org}/{ado_client.project_id}/_apis/build/builds/{build_id}/Timeline'}, 'badge': {'href': 'https://dev.azure.com/{ado_client.org}/{ado_client.project_id}/_apis/build/status/{build_def_id}'}},
    'properties': {},
    'tags': [],
    'validationResults': [],
    'plans': [
        {'planId': '<32_char_id>'}
    ],
    'triggerInfo': {},
    'id': "{build_id}",
    'buildNumber': '20240101.1',
    'status': 'notStarted',
    'queueTime': '2024-03-17T11:03:29.2982876Z',
    'url': 'https://dev.azure.com/{ado_client.org}/{ado_client.project_id}/_apis/build/Builds/{build_id}',
    'definition': {'drafts': [], 'id': "{build_def_id}", 'name': 'ado_wrapper-test-build', 'url': 'https://dev.azure.com/{ado_client.org}/{ado_client.project_id}/_apis/build/Definitions/{build_id}?revision=1', 'uri': 'vstfs:///Build/Definition/{build_id}', 'path': '\\', 'type': 'build', 'queueStatus': 'enabled', 'revision': 1, 'project': {'id': '{ado_client.project_id}', 'name': 'Platform', 'url': 'https://dev.azure.com/{ado_client.org}/_apis/projects/{ado_client.project_id}', 'state': 'wellFormed', 'revision': "{revision}", 'visibility': 'private', 'lastUpdateTime': '2024-01-01T12:14:30.36Z'}},
    'buildNumberRevision': 1,
    'project': {'id': '{ado_client.project_id}', 'name': 'Platform', 'url': 'https://dev.azure.com/{ado_client.org}/_apis/projects/{ado_client.project_id}', 'state': 'wellFormed', 'revision': 399, 'visibility': 'private', 'lastUpdateTime': '2024-02-06T14:14:30.36Z'},
    'uri': 'vstfs:///Build/Build/93458',
    'sourceBranch': 'refs/heads/my-branch',
    'sourceVersion': '<commit_id>',
    'queue': {'id': "{queue_id}", 'name': '<pool_name>', 'pool': {'id': "{pool_id}", 'name': '<pool_name'}},
    'priority': 'normal',
    'reason': 'manual',
    'requestedFor': {'displayName': '<First Last>', 'url': 'https://spsprodweu5.vssps.visualstudio.com/<some_id>/_apis/Identities/<user_id>', '_links': {'avatar': {'href': 'https://dev.azure.com/{ado_client.org}/_apis/GraphProfile/MemberAvatars/<user_descriptor>'}}, 'id': '<user_id>', 'uniqueName': '<first.last@company.com>', 'imageUrl': 'https://dev.azure.com/{ado_client.org}/_apis/GraphProfile/MemberAvatars/<user_descriptor>', 'descriptor': '<user_descriptor>'},
    'requestedBy': {'displayName': '<First Last>', 'url': 'https://spsprodweu5.vssps.visualstudio.com/<some_id>/_apis/Identities/<user_id>', '_links': {'avatar': {'href': 'https://dev.azure.com/{ado_client.org}/_apis/GraphProfile/MemberAvatars/<user_descriptor>'}}, 'id': '<user_id>', 'uniqueName': '<first.last@company.com>', 'imageUrl': 'https://dev.azure.com/{ado_client.org}/_apis/GraphProfile/MemberAvatars/<user_descriptor>', 'descriptor': '<user_descriptor>'},
    'lastChangedDate': '2024-03-17T11:03:29.373Z',
    'lastChangedBy': {'displayName': '<First Last>', 'url': 'https://spsprodweu5.vssps.visualstudio.com/<some_id>/_apis/Identities/<user_id>', '_links': {'avatar': {'href': 'https://dev.azure.com/{ado_client.org}/_apis/GraphProfile/MemberAvatars/<user_descriptor>'}}, 'id': '<user_id>', 'uniqueName': '<first.last@company.com>', 'imageUrl': 'https://dev.azure.com/{ado_client.org}/_apis/GraphProfile/MemberAvatars/<user_descriptor>', 'descriptor': '<user_descriptor>'},
    'orchestrationPlan': {'planId': '<plan_id>'},
    'logs': {'id': 0, 'type': 'Container', 'url': 'https://dev.azure.com/{ado_client.org}/{ado_client.project_id}/_apis/build/builds/93458/logs'},
    'repository': {'id': '<repo_id>', 'type': 'TfsGit', 'name': 'ado_wrapper-test-repo-for-create-delete-builds', 'url': 'https://dev.azure.com/{ado_client.org}/{ado_client.project}/_git/ado_wrapper-test-repo-for-create-delete-builds', 'clean': None, 'checkoutSubmodules': False},
    'retainedByRelease': False,
    'triggeredByBuild': None,
    'appendCommitMessageToRunName': True
}

BUILD_DEFINITION_DUMP = {
    'properties': {},
    'tags': [],
    '_links': {'self': {'href': 'https://dev.azure.com/{ado_client.org}/{ado_client.project_id}/_apis/build/Definitions/2601?revision=1'}, 'web': {'href': 'https://dev.azure.com/{ado_client.org}/{ado_client.project_id}/_build/definition?definitionId=2601'}, 'editor': {'href': 'https://dev.azure.com/{ado_client.org}/{ado_client.project_id}/_build/designer?id=2601&_a=edit-build-definition'}, 'badge': {'href': 'https://dev.azure.com/{ado_client.org}/{ado_client.project_id}/_apis/build/status/2601'}},
    'description': '<description>',
    'jobAuthorizationScope': 'projectCollection',
    'process': {'yamlFilename': 'build.yaml', 'type': 2},
    'repository': {'id': '<repo_id>','type': 'TfsGit', 'name': 'ado_wrapper-test-repo-for-create-delete-builds', 'url': 'https://dev.azure.com/{ado_client.org}/{ado_client.project}/_git/ado_wrapper-test-repo-for-create-delete-builds', 'defaultBranch': 'refs/heads/my-branch', 'clean': None, 'checkoutSubmodules': False},
    'quality': 'definition',
    'authoredBy': {'displayName': '<First> <Last>', 'url': 'https://spsprodweu5.vssps.visualstudio.com/<some_id>/_apis/Identities/<user_id>', '_links': {'avatar': {'href': 'https://dev.azure.com/{ado_client.org}/_apis/GraphProfile/MemberAvatars/<user_descriptor>'}},'id': '<user_id>', 'uniqueName': '<first.last@company.com>', 'imageUrl': 'https://dev.azure.com/{ado_client.org}/_apis/GraphProfile/MemberAvatars/<user_descriptor>', 'descriptor': '<user_descriptor>'},
    'drafts': [],
    'queue': {'_links': {'self': {'href': 'https://dev.azure.com/{ado_client.org}/_apis/build/Queues/575'}}, 'id': 575, 'name': '<pool_name>', 'url': 'https://dev.azure.com/{ado_client.org}/_apis/build/Queues/575', 'pool': {'id': 195, 'name': '<pool_name>'}},
    'id': 2601,
    'name': 'ado_wrapper-test-build',
    'url': 'https://dev.azure.com/{ado_client.org}/{ado_client.project_id}/_apis/build/Definitions/2601?revision=1',
    'uri': 'vstfs:///Build/Definition/2601',
    'path': '\\',
    'type': 'build',
    'queueStatus': 'enabled',
    'revision': 1,
    'createdDate': '2024-03-17T11:03:28.943Z',
    'project': {'id': '{ado_client.project_id}', 'name': '{ado_client.project}', 'url': 'https://dev.azure.com/{ado_client.org}/_apis/projects/{ado_client.project_id}', 'state': 'wellFormed', 'revision': 399, 'visibility': 'private', 'lastUpdateTime': '2024-02-06T14:14:30.36Z'}
}

COMMIT_DUMP = {
    'commitId': '<commit_id>',
    'author': {'name': '<First Last>', 'email': '<first.last@company.com>', 'date': '2024-03-17T11:45:19Z'},
    'committer': {'name': '<First Last>', 'email': '<first.last@company.com>', 'date': '2024-03-17T11:45:19Z'},
    'comment': 'Add README.md',
    'changeCounts': {'Add': 1, 'Edit': 0, 'Delete': 0},
    'url': 'https://dev.azure.com/{ado_client.org}/{ado_client.project_id}/_apis/git/repositories/<repo_id>/commits/<commit_id>',
    'remoteUrl': 'https://dev.azure.com/{ado_client.org}/{ado_client.project}/_git/ado_wrapper-test-repo-for-create-delete-builds/commit/<other_commit_id>',
}

GROUP_DUMP = {
    'subjectKind': 'group',
    'description': '{description}',
    'domain': 'vstfs:///Classification/TeamProject/{group_id}',
    'principalName': 'Our Team Name',
    'mailAddress': None,
    'origin': 'vsts',
    'originId': '{originId}',
    'displayName': 'Our Team',
    '_links': {'self': {'href': 'https://vssps.dev.azure.com/{ado_client.org}/_apis/Graph/Groups/{subject_descriptor}'}, 'memberships': {'href': 'https://vssps.dev.azure.com/{ado_client.org}/_apis/Graph/Memberships/{subject_descriptor}'}, 'membershipState': {'href': 'https://vssps.dev.azure.com/{ado_client.org}/_apis/Graph/MembershipStates/{subject_descriptor}'}, 'storageKey': {'href': 'https://vssps.dev.azure.com/{ado_client.org}/_apis/Graph/StorageKeys/{subject_descriptor}'}},
    'url': 'https://vssps.dev.azure.com/{ado_client.org}/_apis/Graph/Groups/{subject_descriptor}'}


PROJECT_DUMP = {
    'id': '<32_char_uuid>',
    'name': '<project_name>',
    'description': '<description>',
    'url': 'https://dev.azure.com/{ado_client.org}/_apis/projects/<project_id>',
    'state': 'wellFormed',
    'revision': 194,
    'visibility': 'private',
    'lastUpdateTime': '2024-03-18T16:41:05.14Z',
}

PULL_REQUEST_DUMP = {
    'repository ': {'id': '<repo_id>', 'name': 'ado_wrapper-test-repo-for-get-pull-request-by-id', 'url': 'https://dev.azure.com/{ado_client.org}/{ado_client.project_id}/_apis/git/repositories/<repo_id>', 'project': {'id': '<project_id>', 'name': '<project_name>', 'url': 'https://dev.azure.com/{ado_client.org}/_apis/projects/{ado_client.project_id}', 'state': 'wellFormed', 'revision': 399, 'visibility': 'private', 'lastUpdateTime': '2024-02-06T14:14:30.36Z'}, 'size': 980, 'remoteUrl': 'https://{ado_client.org}@dev.azure.com/{ado_client.org}/{ado_client.project}/_git/ado_wrapper-test-repo-for-get-pull-request-by-id', 'sshUrl': 'git@ssh.dev.azure.com:v3/{ado_client.org}/{ado_client.project}/ado_wrapper-test-repo-for-get-pull-request-by-id', 'webUrl': 'https://dev.azure.com/{ado_client.org}/{ado_client.project}/_git/ado_wrapper-test-repo-for-get-pull-request-by-id', 'isDisabled': False, 'isInMaintenance': False},
    'pullRequestId': "{pull_request_id}",
    'codeReviewId': "{code_review_id}",
    'status': 'active',
    'createdBy': {'displayName': '<First Last>', 'url': 'https://spsprodweu5.vssps.visualstudio.com/<some_id>/_apis/Identities/<user_id>', '_links': {'avatar': {'href': 'https://dev.azure.com/{ado_client.org}/_apis/GraphProfile/MemberAvatars/<user_descriptor>'}}, 'id': '<user_id>', 'uniqueName': '<first.last@company.com>', 'imageUrl': 'https://dev.azure.com/{ado_client.org}/_api/_common/identityImage?id=<user_id>', 'descriptor': '<user_descriptor>'},
    'creationDate': '2021-03-17T11:18:39.9163346Z',
    'title': '<title>',
    'description': '<description>',
    'sourceRefName': 'refs/heads/test-branch',
    'targetRefName': 'refs/heads/main',
    'mergeStatus': 'succeeded',
    'isDraft': False,
    'mergeId': '<32_char_uuid>',
    'lastMergeSourceCommit': {'commitId': '<commit_id>', 'url': 'https://dev.azure.com/{ado_client.org}/{ado_client.project_id}/_apis/git/repositories/<repo_id>/commits/<commit_id>'},
    'lastMergeTargetCommit': {'commitId': '<commit_id>', 'url': 'https://dev.azure.com/{ado_client.org}/{ado_client.project_id}/_apis/git/repositories/<repo_id>/commits/<commit_id>'},
    'lastMergeCommit': {'commitId': '<commit_id>', 'author': {'name': '<First Last>', 'email': '<first.last@company.com>', 'date': '2024-03-17T11:18:40Z'}, 'committer': {'name': '<First Last>', 'email': '<first.last@company.com>', 'date': '2024-03-17T11:18:40Z'}, 'comment': '<comment>', 'url': 'https://dev.azure.com/{ado_client.org}/{ado_client.project_id}/_apis/git/repositories/<repo_id>/commits/<commit_id>'},
    'reviewers': [],
    'url': 'https://dev.azure.com/{ado_client.org}/{ado_client.project_id}/_apis/git/repositories/<repo_id>/pullRequests/10237',
    '_links': {'self': {'href': 'https://dev.azure.com/{ado_client.org}/{ado_client.project_id}/_apis/git/repositories/<repo_id>/pullRequests/10237'}, 'repository': {'href': 'https://dev.azure.com/{ado_client.org}/{ado_client.project_id}/_apis/git/repositories/<repo_id>'}, 'workItems': {'href': 'https://dev.azure.com/{ado_client.org}/{ado_client.project_id}/_apis/git/repositories/<repo_id>/pullRequests/10237/workitems'}, 'sourceBranch': {'href': 'https://dev.azure.com/{ado_client.org}/{ado_client.project_id}/_apis/git/repositories/<repo_id>/refs/heads/test-branch'}, 'targetBranch': {'href': 'https://dev.azure.com/{ado_client.org}/{ado_client.project_id}/_apis/git/repositories/<repo_id>/refs/heads/main'}, 'statuses': {'href': 'https://dev.azure.com/{ado_client.org}/{ado_client.project_id}/_apis/git/repositories/<repo_id>/pullRequests/10237/statuses'}, 'sourceCommit': {'href': 'https://dev.azure.com/{ado_client.org}/{ado_client.project_id}/_apis/git/repositories/<repo_id>/commits/<commit_id>'}, 'targetCommit': {'href': 'https://dev.azure.com/{ado_client.org}/{ado_client.project_id}/_apis/git/repositories/<repo_id>/commits/<commit_id>'}, 'createdBy': {'href': 'https://spsprodweu5.vssps.visualstudio.com/<some_id>/_apis/Identities/<user_id>'}, 'iterations': {'href': 'https://dev.azure.com/{ado_client.org}/{ado_client.project_id}/_apis/git/repositories/<repo_id>/pullRequests/10237/iterations'}},
    'supportsIterations': True,
    'artifactId': 'vstfs:///Git/PullRequestId/<project_id>%2f<repo_id>%2f10237'
}

REPO_DUMP = {
    'id': '<repo_id>',
    'name': '{repo_name}',
    'url': 'https://dev.azure.com/{ado_client.org}/{ado_client.project_id}/_apis/git/repositories/{self.repo_id}',
    'project': {'id': '{ado_client.project_id}', 'name': '{<project_name>}', 'url': 'https://dev.azure.com/{ado_client.org}/_apis/projects/{ado_client.project_id}', 'state': 'wellFormed', 'revision': 399, 'visibility': 'private', 'lastUpdateTime': '2024-02-06T14:14:30.36Z'},
    'size': 0,
    'remoteUrl': 'https://{ado_client.org}@dev.azure.com/{ado_client.org}/{ado_client.project}/_git/{repo_name}',
    'sshUrl': 'git@ssh.dev.azure.com:v3/{ado_client.org}/{ado_client.project}/{repo_name}',
    'webUrl': 'https://dev.azure.com/{ado_client.org}/{ado_client.project}/_git/{repo_name}',
    'isDisabled': False,
    'isInMaintenance': False,
}

SERVICE_ENDPOINT_DUMP = {
    'data': {},
    'id': '{service_endpoint_id}',
    'name': '{service_connection_name}',
    'type': 'github',
    'url': 'https://github.com',
    'createdBy': "<Member>",
    'description': '{description}',
    'authorization': {'parameters': {'AccessToken': None}, 'scheme': 'Token'},
    'isShared': False,
    'isOutdated': False, 'isReady': True,
    'owner': 'Library',
    'serviceEndpointProjectReferences': [{'projectReference': {'id': '{project_id}', 'name': '{project_name}'},
                                          'name': '{service_connection_name}', 'description': '{description}'}]
}

TEAM_DUMP = {
    'id': '<32_char_uuid>',
    'name': 'Systems Team',
    'url': 'https://dev.azure.com/{ado_client.org}/_apis/projects/{ado_client.project_id}/teams/<32_char_uuid>',
    'description': '<description>',
    'identityUrl': 'https://spsprodweu5.vssps.visualstudio.com/<some_id>/_apis/Identities/<32_char_uuid>',
    'projectName': '<project_name',
    'projectId': '<32_char_uuid>'
}

VARIABLE_GROUP_DUMP = {
    'variables': {'a': {'value': 'b', 'isReadOnly': True}},
    'id': 528,
    'type': 'Vsts',
    'name': 'ado_wrapper-test-for-create-delete',
    'description': 'my_description',
    'createdBy': {'displayName': None, 'id': '<user_id>'},
    'createdOn': '2024-03-17T11:04:25.4233333Z',
    'modifiedBy': {'displayName': None, 'id': '<user_id>'},
    'modifiedOn': '2024-03-17T11:04:25.4233333Z',
    'isShared': False,
    'variableGroupProjectReferences': [
        {'projectReference': {'id': '{ado_client.project_id}', 'name': '<project_name'}, 'name': '{repo_name}', 'description': '{description}'}
    ]
}
