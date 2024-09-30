import pytest

if __name__ == "__main__":
    __import__("sys").path.insert(0, __import__("os").path.abspath(__import__("os").path.dirname(__file__) + "/.."))

from ado_wrapper.resources.merge_policies import MergePolicies, MergeBranchPolicy, MergeTypeRestrictionPolicy
from tests.setup_client import RepoContextManager, existing_user_id, setup_client


class TestMergePolicy:
    def setup_method(self) -> None:
        self.ado_client = setup_client()

    @pytest.mark.create_delete
    def test_create_branch_policy(self) -> None:
        with RepoContextManager(self.ado_client, "create-branch-policy") as repo:
            MergePolicies.set_branch_policy(self.ado_client, repo.repo_id, 3, False, False, False, "do_nothing")
            policy = MergePolicies.get_branch_policy(self.ado_client, repo.repo_id)
            assert policy is not None
            assert policy.minimum_approver_count == 3
            assert not policy.creator_vote_counts
            assert not policy.prohibit_last_pushers_vote
            assert not policy.allow_completion_with_rejects
            assert policy.when_new_changes_are_pushed == "do_nothing"

    @pytest.mark.update
    def test_update_branch_policy(self) -> None:
        with RepoContextManager(self.ado_client, "update-branch-policy") as repo:
            MergePolicies.set_branch_policy(self.ado_client, repo.repo_id, 3, False, False, False, "do_nothing")

            policy = MergePolicies.get_branch_policy(self.ado_client, repo.repo_id)
            assert policy is not None

            MergePolicies.set_branch_policy(self.ado_client, repo.repo_id, 4, True, True, True, "require_revote_on_each_iteration")
            updated_policy = MergePolicies.get_branch_policy(self.ado_client, repo.repo_id)
            assert updated_policy is not None
            assert updated_policy.minimum_approver_count == 4
            assert updated_policy.creator_vote_counts
            assert updated_policy.prohibit_last_pushers_vote
            assert updated_policy.allow_completion_with_rejects
            assert updated_policy.when_new_changes_are_pushed == "require_revote_on_each_iteration"

    @pytest.mark.hierarchy
    @pytest.mark.create_delete
    def test_create_default_reviewer(self) -> None:
        with RepoContextManager(self.ado_client, "create-default-reviewer") as repo:
            MergePolicies.add_default_reviewer(self.ado_client, repo.repo_id, existing_user_id, False)
            default_reviewers = MergePolicies.get_default_reviewers(self.ado_client, repo.repo_id)
            assert default_reviewers is not None
            assert len(default_reviewers) == 1
            assert default_reviewers[0].member_id == existing_user_id
            assert not default_reviewers[0].is_required

            with pytest.raises(ValueError):  # Can't add them twice
                MergePolicies.add_default_reviewer(self.ado_client, repo.repo_id, existing_user_id, True)

            MergePolicies.remove_default_reviewer(self.ado_client, repo.repo_id, existing_user_id)
            default_reviewers = MergePolicies.get_default_reviewers(self.ado_client, repo.repo_id)
            assert not default_reviewers
            # We also need to do way more work with the "inheritedPolicies" field, currently, "currentScopePolicies" is None for many, this
            # Might not actually be a problem though, idk

    @pytest.mark.create_delete
    def test_create_merge_type_restriction_policy(self) -> None:
        with RepoContextManager(self.ado_client, "create-delete-merge-type-restriction") as repo:
            no_policy = MergePolicies.get_allowed_merge_types(self.ado_client, repo.repo_id)
            assert no_policy is None
            MergePolicies.set_allowed_merge_types(self.ado_client, repo.repo_id, True, False, True, False)
            allowed_merge_types = MergePolicies.get_allowed_merge_types(self.ado_client, repo.repo_id)
            assert allowed_merge_types is not None
            assert allowed_merge_types.allow_basic_no_fast_forwards
            assert not allowed_merge_types.allow_squash
            assert allowed_merge_types.allow_rebase_and_fast_forward
            assert not allowed_merge_types.allow_rebase_with_merge_commit

    @pytest.mark.wip
    def test_get_all_repo_policies(self) -> None:
        with RepoContextManager(self.ado_client, "get-all-repo-policies") as repo:
            policies = MergePolicies.get_all_repo_policies(self.ado_client, repo.repo_id)
            assert isinstance(policies, tuple)
            assert len(policies) == 3
            assert isinstance(policies[0], list)
            assert isinstance(policies[1], (MergeBranchPolicy, type(None)))
            assert isinstance(policies[2], (MergeTypeRestrictionPolicy, type(None)))


if __name__ == "__main__":
    # pytest.main([__file__, "-s", "-vvvv"])
    pytest.main([__file__, "-s", "-vvvv", "-m", "wip"])
