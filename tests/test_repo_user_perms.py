import pytest

from ado_wrapper.resources.repo_user_permission import RepoUserPermissions, UserPermission, PermissionType, ActionType
from tests.setup_client import setup_client, RepoContextManager, email, existing_user_name


class TestRepoUserPerms:
    def setup_method(self) -> None:
        self.ado_client = setup_client()

    @pytest.mark.from_request_payload
    def test_from_request_payload(self) -> None:
        repo_user_perms = UserPermission.from_request_payload(
            {
                'displayName': 'Bypass policies when completing pull requests',
                'namespaceId': '2e9eb7ed-3c0a-47d4-87c1-0ffdd275fd87',
                'token': 'repoV2/project_id/repo_id/',
                'bit': 32768,
                'canEdit': True,
                'effectivePermissionValue': 1,
                'explicitPermissionValue': 1,
                'permissionDisplayString': 'Allow'
            }
        )
        assert isinstance(repo_user_perms, UserPermission)
        assert repo_user_perms.namespace_id == "2e9eb7ed-3c0a-47d4-87c1-0ffdd275fd87"
        assert repo_user_perms.display_name == "bypass_policies_when_completing_pull_requests"
        assert repo_user_perms.token == "repoV2/project_id/repo_id/"
        assert repo_user_perms.bit == 32768
        assert repo_user_perms.can_edit
        assert repo_user_perms.permission_display_string == "Allow"

    @pytest.mark.create_delete
    def test_create_delete(self) -> None:
        with RepoContextManager(self.ado_client, "create-repo-user-perms") as repo:
            RepoUserPermissions.set_by_subject_email(self.ado_client, repo.repo_id, email, "Allow", "contribute")
            perms = RepoUserPermissions.get_by_subject_email(self.ado_client, repo.repo_id, email)
            assert isinstance(perms, list)
            assert all(isinstance(x, UserPermission) for x in perms)
            assert [x for x in perms if x.display_name == "contribute"][0].permission_display_string == "Allow"

    @pytest.mark.get_all
    def test_get_all(self) -> None:
        with RepoContextManager(self.ado_client, "create-get-all-user-perms") as repo:
            RepoUserPermissions.set_by_subject_email(self.ado_client, repo.repo_id, email, "Allow", "contribute")
            all_perms = RepoUserPermissions.get_all_by_repo_id(self.ado_client, repo.repo_id)
            assert existing_user_name in all_perms
            assert isinstance(all_perms[existing_user_name], list)
            assert [x for x in all_perms[existing_user_name] if x.display_name == "contribute"][0].permission_display_string == "Allow"

    def test_set_by_subject_email_batch(self) -> None:
        with RepoContextManager(self.ado_client, "set-by-subject-email-batch") as repo:
            input_perms: dict[PermissionType, ActionType] = {
                "bypass_policies_when_completing_pull_requests": "Allow",
                "bypass_policies_when_pushing": "Allow",
                "contribute": "Allow",
                "contribute_to_pull_requests": "Deny",
                "create_branch": "Allow",
                "create_tag": "Deny",
                "delete_or_disable_repository": "Allow",
                "edit_policies": "Allow",
                "force_push": "Allow",
                "manage_notes": "Deny",
                "manage_permissions": "Allow",
                "read": "Allow",
                "remove_others_locks": "Deny",
                "rename_repository": "Deny",
            }
            RepoUserPermissions.set_by_subject_email_batch(self.ado_client, repo.repo_id, email, input_perms)
            all_perms = RepoUserPermissions.get_all_by_repo_id(self.ado_client, repo.repo_id)
            perms_formatted = {perm.display_name: perm.permission_display_string for perm in all_perms[existing_user_name]}
            assert perms_formatted == input_perms

    def test_set_all_permissions_for_repo(self) -> None:
        with RepoContextManager(self.ado_client, "set-by-subject-email-batch") as repo:
            input_perms: dict[str, dict[PermissionType, ActionType]] = {
                email: {
                    "bypass_policies_when_completing_pull_requests": "Allow",
                    "bypass_policies_when_pushing": "Allow",
                    "contribute": "Allow",
                    "contribute_to_pull_requests": "Deny",
                    "create_branch": "Allow",
                    "create_tag": "Deny",
                    "delete_or_disable_repository": "Allow",
                    "edit_policies": "Allow",
                    "force_push": "Allow",
                    "manage_notes": "Deny",
                    "manage_permissions": "Allow",
                    "read": "Allow",
                    "remove_others_locks": "Deny",
                    "rename_repository": "Deny",
                }
            }
            RepoUserPermissions.set_all_permissions_for_repo(self.ado_client, repo.repo_id, input_perms)
            all_perms = RepoUserPermissions.get_all_by_repo_id(self.ado_client, repo.repo_id)
            perms_formatted: dict[PermissionType, ActionType] = {perm.display_name: perm.permission_display_string  # type: ignore[misc]
                                                                 for perm in all_perms[existing_user_name]}
            assert perms_formatted == input_perms  # type: ignore[comparison-overlap]

    def test_remove_perms(self) -> None:
        with RepoContextManager(self.ado_client, "remove-perms") as repo:
            RepoUserPermissions.set_by_subject_email(self.ado_client, repo.repo_id, email, "Allow", "contribute")
            perms = RepoUserPermissions.get_by_subject_email(self.ado_client, repo.repo_id, email)
            assert isinstance(perms, list)
            assert all(isinstance(x, UserPermission) for x in perms)
            assert [x for x in perms if x.display_name == "contribute"][0].permission_display_string == "Allow"

            RepoUserPermissions.remove_perm(self.ado_client, repo.repo_id, email)
            updated_perms = RepoUserPermissions.get_all_by_repo_id(self.ado_client, repo.repo_id)
            assert email not in updated_perms
