import pytest

from ado_wrapper.resources.annotated_tags import AnnotatedTag
from ado_wrapper.resources.commits import Commit

from tests.setup_client import setup_client, RepoContextManager


class TestAnnotatedTags:
    def setup_method(self) -> None:
        self.ado_client = setup_client()

    @pytest.mark.from_request_payload
    def test_from_request_payload(self) -> None:
        tag = AnnotatedTag.from_request_payload(
            {
                "objectId": "aaaa-aa-aaaa",
                "name": "tag_name",
                "message": "tag_message",
                "taggedBy": {"name": "TestUser", "email": "test@company.com", "date": "2021-10-01T00:00:00Z"},
            }
        )
        assert tag.to_json() == AnnotatedTag.from_json(tag.to_json()).to_json()

    @pytest.mark.create_delete
    def test_create_delete_tag(self) -> None:
        with RepoContextManager(self.ado_client, "create-delete-tag") as repo:
            commit = Commit.create(self.ado_client, repo.repo_id, "main", "test-tag", {"text.txt": "Contents"}, "add", "Commmit 1")
            AnnotatedTag.create(self.ado_client, repo.repo_id, "test-tag", "Test tag message", commit.commit_id)
            tags = AnnotatedTag.get_all_by_repo(self.ado_client, repo.repo_id)
            assert len(tags) == 1
            with pytest.raises(NotImplementedError):
                tags[0].delete(self.ado_client)

    def test_get_certain_tages(self) -> None:
        with RepoContextManager(self.ado_client, "get-certain-tags") as repo:
            commit1 = Commit.create(self.ado_client, repo.repo_id, "main", "test-tag-1", {"text.txt": "Contents"}, "add", "Commmit 1")
            commit2 = Commit.create(self.ado_client, repo.repo_id, "main", "test-tag-2", {"text2.txt": "Contents"}, "add", "Commmit 2")
            AnnotatedTag.create(self.ado_client, repo.repo_id, "test-tag-1", "Test tag message 1", commit1.commit_id)
            AnnotatedTag.create(self.ado_client, repo.repo_id, "test-tag-2", "Test tag message 2", commit2.commit_id)
            tag = AnnotatedTag.get_by_name(self.ado_client, repo.repo_id, "test-tag-1")
            assert tag is not None
            assert tag.name == "test-tag-1"
            for tag in AnnotatedTag.get_all_by_repo(self.ado_client, repo.repo_id):
                with pytest.raises(NotImplementedError):
                    tag.delete(self.ado_client)
