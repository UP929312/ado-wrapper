import pytest

from ado_wrapper.resources.annotated_tags import AnnotatedTag
from ado_wrapper.resources.commits import Commit
from tests.setup_client import RepoContextManager, setup_client

if __name__ == "__main__":
    __import__("sys").path.insert(0, __import__("os").path.abspath(__import__("os").path.dirname(__file__) + "/.."))


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
                "url": "https://dev.azure.com/organization/project/_apis/git/repositories/repo_id/annotatedtags/aaaa-aa-aaaa",
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
            tags[0].delete(self.ado_client)
            new_tags = AnnotatedTag.get_all_by_repo(self.ado_client, repo.repo_id)
            assert len(new_tags) == 0

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
                tag.delete(self.ado_client)

    def test_get_all_annonated_tags(self) -> None:
        with RepoContextManager(self.ado_client, "get-all-annotated-tags") as repo:
            commit1 = Commit.create(self.ado_client, repo.repo_id, "main", "test-tag-1", {"text.txt": "Contents"}, "add", "Commmit 1")
            commit2 = Commit.create(self.ado_client, repo.repo_id, "main", "test-tag-2", {"text2.txt": "Contents"}, "add", "Commmit 2")
            AnnotatedTag.create(self.ado_client, repo.repo_id, "test-tag-1", "Test tag message 1", commit1.commit_id)
            AnnotatedTag.create(self.ado_client, repo.repo_id, "test-tag-2", "Test tag message 2", commit2.commit_id)
            tags = AnnotatedTag.get_all_by_repo(self.ado_client, repo.repo_id)
            assert len(tags) == 2
            for tag in tags:
                tag.delete(self.ado_client)


if __name__ == "__main__":
    # pytest.main([__file__, "-s", "-vvvv"])
    pytest.main([__file__, "-s", "-vvvv", "-m", "wip"])
