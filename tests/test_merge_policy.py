import pytest

from ado_wrapper.resources.repo import Repo
from ado_wrapper.resources.merge_policies import MergePolicies

from tests.setup_client import setup_client, existing_user_id


class TestMergePolicy:
    def setup_method(self) -> None:
        self.ado_client = setup_client()

    @pytest.mark.create_delete
    def test_create_branch_policy(self) -> None:
        repo = Repo.create(self.ado_client, "ado_wrapper-test-repo-for-create-branch-policy")
        MergePolicies.set_branch_policy(self.ado_client, repo.repo_id, 3, False, False, False, "do_nothing")
        policy = MergePolicies.get_branch_policy(self.ado_client, repo.repo_id)
        assert policy is not None
        assert policy.minimum_approver_count == 3
        assert not policy.creator_vote_counts
        assert not policy.prohibit_last_pushers_vote
        assert not policy.allow_completion_with_rejects
        assert policy.when_new_changes_are_pushed == "do_nothing"
        repo.delete(self.ado_client)

    @pytest.mark.update
    def test_update_branch_policy(self) -> None:
        repo = Repo.create(self.ado_client, "ado_wrapper-test-repo-for-update-branch-policy")
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
        repo.delete(self.ado_client)

    @pytest.mark.create_delete
    @pytest.mark.wip
    def test_create_default_reviewer(self) -> None:
        repo = Repo.create(self.ado_client, "ado_wrapper-test-repo-for-create-default-reviewer")
        MergePolicies.add_default_reviewer(self.ado_client, repo.repo_id, existing_user_id, False)
        default_reviewers = MergePolicies.get_default_reviewers(self.ado_client, repo.repo_id)
        assert default_reviewers is not None
        assert len(default_reviewers) == 1
        assert default_reviewers[0].member_id == existing_user_id
        assert not default_reviewers[0].is_required

        with pytest.raises(ValueError):
            MergePolicies.add_default_reviewer(self.ado_client, repo.repo_id, existing_user_id, True)

        MergePolicies.remove_default_reviewer(self.ado_client, repo.repo_id, existing_user_id)
        default_reviewers = MergePolicies.get_default_reviewers(self.ado_client, repo.repo_id)
        assert not default_reviewers
        repo.delete(self.ado_client)

        # We also need to do way more work with the "inheritedPolicies" field, currently, "currentScopePolicies" is None for many, this
        # Might not actually be a problem though, idk
