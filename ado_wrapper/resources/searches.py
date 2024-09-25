from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Literal

from ado_wrapper.errors import ConfigurationError

if TYPE_CHECKING:
    from ado_wrapper.client import AdoClient

SortDirections = Literal["ASC", "DESC"]


@dataclass
class CodeSearch:
    """https://learn.microsoft.com/en-us/rest/api/azure/devops/search/code-search-results/fetch-code-search-results"""

    repository_name: str
    path: str
    file_name: str = field(repr=False)
    project: str = field(repr=False)
    repository_id: str = field(repr=False)
    branch_name: str = field(repr=False)
    matches: list["CodeSearchHit"] = field(default_factory=list, repr=False)

    # 'versions': [{'branchName': 'main', 'changeId': 'f8a3262a0b2fa01ea4fde05881432628d5969dc6'}], 'contentId': 'c7f221fdfaea814aa742cc2d10eb0655645f101f'}
    # 'versions': [{'branchName': 'main', 'changeId': 'd53915b6d1b1b30d94e66fd19b99f2f2d2a1c3e3'}], 'contentId': 'a03f69e0c43e3bfc4b933bf89e2b2b8253b3ba7a'}

    @classmethod
    def from_request_payload(cls, data: dict[str, Any]) -> "CodeSearch":
        return cls(
            repository_name=data["repository"]["name"],
            path=data["path"],
            file_name=data["fileName"],
            project=data["project"]["name"],
            repository_id=data["repository"]["id"],
            branch_name=data["versions"][0]["branchName"],
            matches=[CodeSearchHit.from_request_payload(x) for x in data["matches"]["content"]],
        )

    @classmethod
    def get_by_search_string(
        cls, ado_client: "AdoClient", search_text: str, result_count: int = 1000, sort_direction: SortDirections = "ASC"
    ) -> list["CodeSearch"]:
        if not 0 < result_count <= 1000:
            raise ConfigurationError("Error, result_count must be between 1 and 1000 (inclusive)")
        body = {
            "$orderBy": [{"field": "filename", "sortOrder": sort_direction}],  # fmt: skip
            "$top": result_count,
            "filters": "",
            "includeFacets": "true",
            "includeSnippet": "true",
            "searchText": search_text,
            # "$skip": 0,  # TODO Probably add this later for getting the next page, it should probably be page_number * result_count
        }
        data = ado_client.session.post(
            f"https://almsearch.dev.azure.com/{ado_client.ado_org_name}/{ado_client.ado_project_name}/_apis/search/codesearchresults?api-version=7.0",
            json=body,
        ).json()
        if data.get("message") == "The extension ms.vss-code-search is not installed.":
            raise ConfigurationError(data["message"])
        return [cls.from_request_payload(x) for x in data["results"]]


@dataclass
class CodeSearchHit:
    char_offset: int
    length: int
    line: int
    column: int
    code_snippet: str | None
    hit_type: str  # One of `content`, <more>

    @classmethod
    def from_request_payload(cls, data: dict[str, Any]) -> "CodeSearchHit":
        # {'charOffset': 49170, 'length': 8, 'line': 0, 'column': 0, 'codeSnippet': None, 'type': 'content'}
        return cls(
            data["charOffset"], data["length"], data["line"], data["column"], data["codeSnippet"], data["type"],  # fmt: skip
        )
