from typing import Callable, Any
import re
from datetime import datetime

import requests

class UnknownUntilApply(str):
    def __str__(self) -> str:
        return "Unknown until apply"
UnknownUntilApply = UnknownUntilApply()  # type: ignore


class FakeResponse(requests.Response):
    def __init__(self, _json: dict[str, Any], status_code: int) -> None:
        super().__init__()
        self._json = _json
        self.status_code = status_code

    def json(self) -> dict[str, Any]:  # type: ignore[override]
        return self._json

CreateMethod = Callable[[str, dict[str, Any], Any], FakeResponse]


class PlanRepo:
    method_types = {
        "create": "post",
    }

    @staticmethod
    def create(url: str, *, json: dict[str, Any], auth: Any) -> FakeResponse:
        """This is what requests.<x> will get set with, so should have the same signature as the requests.<x> method."""
        # if re.match()
        if "/git/repositories?" in url:  # When we're creating the repo
            return FakeResponse({'id': UnknownUntilApply, 'name': json["name"], 'isDisabled': False,}, 200)
        elif "/pushes" in url:
            #member = Member(data["author"]["name"], data["author"]["email"], "UNKNOWN")
            # return cls(data["commitId"], member, from_ado_date_string(data["author"]["date"]), data["comment"])
            return FakeResponse({
                "commitId": UnknownUntilApply,
                "author": {"name": "test", "email": "test", "date": datetime.now().isoformat()},
                "comment": "Add README.md",
            }, 200)
        return FakeResponse({}, 404)