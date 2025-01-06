from datetime import datetime

import pytest

if __name__ == "__main__":
    __import__("sys").path.insert(0, __import__("os").path.abspath(__import__("os").path.dirname(__file__) + "/.."))

from ado_wrapper.state_managed_abc import convert_from_json, recursively_convert_to_json
from ado_wrapper.resources.pull_requests import PullRequest
from ado_wrapper.resources.users import Member, Reviewer
from ado_wrapper.resources.repo import Repo


class TestStateManagedABCs:
    def test_recursively_convert_to_json(self) -> None:
        now = datetime.now()
        raw_input = {
            "id": "123",
            "number": 456,
            "boolean": True,
            "dt_object": now,
            "dict": {"key": "value", "nested": {"key2": "value2"}},
            "list": [1, 2, 3],
        }
        data = dict(recursively_convert_to_json(attribute_name, attribute_value) for attribute_name, attribute_value in raw_input.items())
        assert data == {
            "id": "123",
            "number": "456",
            "boolean": "True",
            "dt_object::datetime": now.isoformat(),
            "dict": {"key": "value", "nested": {"key2": "value2"}},
            "list": ["1", "2", "3"],
        }

    def test_recursively_convert_from_json(self) -> None:
        now = datetime.now()
        raw_input = {
            "id": "123",
            "number": "456",
            "boolean": True,
            "dt_object::datetime": now.isoformat(),
            "dict": {"key": "value", "nested": {"key2": "value2"}},
            "list": ["1", "2", "3"],
        }
        data = convert_from_json(raw_input)
        assert data == {
            "id": "123",
            "number": "456",
            "boolean": True,
            "dt_object": now,
            "dict": {"key": "value", "nested": {"key2": "value2"}},
            "list": ["1", "2", "3"],
        }

    @pytest.mark.wip
    def test_convert_to_and_from_json(self) -> None:
        pull_request = PullRequest(
            "123",
            "Test Pull Request",
            "Test Description",
            "source-branch",
            "target-branch",
            "000000000",
            "111111111",
            Member("name", "email", "123"),
            datetime.now(),
            Repo("123", "name", default_branch="target-branch"),
            datetime.now(),
            False,
            "completed",
            "succeeded",
            reviewers=[Reviewer("reviewer-name", "reviewer-email", "123", 10)],
        )
        pull_request_json = pull_request.to_json()
        pull_request_converted = PullRequest.from_json(pull_request_json)
        assert isinstance(pull_request_converted.reviewers[0], Reviewer)


if __name__ == "__main__":
    pytest.main([__file__, "-s", "-vvvv"])
    # pytest.main([__file__, "-s", "-vvvv", "-m", "wip"])
