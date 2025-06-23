from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Literal, Generator

from ado_wrapper.state_managed_abc import StateManagedResource

if TYPE_CHECKING:
    from ado_wrapper.client import AdoClient


WikiType = Literal["project_wiki", "code_wiki"]
wiki_type_int_to_name: dict[int, WikiType] = {
    0: "project_wiki",
    1: "code_wiki",
}


@dataclass
class Wiki(StateManagedResource):
    """https://learn.microsoft.com/en-us/rest/api/azure/devops/wiki/wikis?view=azure-devops-rest-7.1"""
    wiki_id: str = field(metadata={"is_id_field": True})
    wiki_type: WikiType
    wiki_name: str
    wiki_repo_id: str

    @classmethod
    def from_request_payload(cls, data: dict[str, Any]) -> "Wiki":
        return cls(
            str(data["id"]),
            wiki_type_int_to_name[data["type"]],
            data["name"],
            data["repositoryId"]
        )

    @classmethod
    def get_by_id(cls, ado_client: "AdoClient", wiki_id: str) -> "Wiki":
        return super()._get_by_url(
            ado_client,
            f"https://dev.azure.com/{ado_client.ado_org_name}/{ado_client.ado_project_name}/_apis/wiki/wikis/{wiki_id}?api-version=7.1",
        )  # pyright: ignore[reportReturnType]

    @classmethod
    def get_all(cls, ado_client: "AdoClient") -> list["Wiki"]:
        return super()._get_by_url(
            ado_client,
            f"https://dev.azure.com/{ado_client.ado_org_name}/{ado_client.ado_project_name}/_apis/wiki/wikis?api-version=7.1",
            fetch_multiple=True,
        )  # pyright: ignore[reportReturnType]

    def link(self, ado_client: "AdoClient") -> str:
        # https://dev.azure.com/vfuk-digital/Digital/_wiki/wikis/Digital%20X.wiki/
        return f"https://dev.azure.com/{ado_client.ado_org_name}/{ado_client.ado_project_name}/_wiki/wikis/{self.wiki_name}.wiki/"

    # ============ End of requirement set by all state managed resources ================== #
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
    # =============== Start of additional methods included with class ===================== #

    @classmethod
    def get_by_name(cls, ado_client: "AdoClient", name: str) -> "Wiki | None":
        return cls._get_by_abstract_filter(ado_client, lambda wiki: wiki.wiki_name == name)


@dataclass
class WikiPage(StateManagedResource):
    """https://learn.microsoft.com/en-us/rest/api/azure/devops/wiki/pages?view=azure-devops-rest-7.1"""
    wiki_page_id: str = field(metadata={"is_id_field": True})
    wiki_page_path: str
    wiki_page_content: str
    wiki_id: str

    @classmethod
    def from_request_payload(cls, data: dict[str, Any]) -> "WikiPage":
        return cls(
            str(data["id"]),
            data["path"],
            data["content"],
            data["wikiId"]
        )

    @classmethod
    def download_page_contents(cls, ado_client: "AdoClient", wiki_id: str, wiki_page_path: str) -> str:
        """Downloads the content of the wiki page."""
        request = ado_client.session.get(
            f"https://dev.azure.com/{ado_client.ado_org_name}/{ado_client.ado_project_name}/_apis/wiki/wikis/{wiki_id}/pages?path={wiki_page_path}&recursionLevel=1&versionDescriptor.version=wikiMaster",
            headers={"Accept": "text/html"}
        )
        # Changing the headers returns metadata, this returns content
        return request.text

    @classmethod
    def get_page_metadata(cls, ado_client: "AdoClient", wiki_id: str, wiki_page_path: str) -> dict[str, Any]:
        """Fetches metadata for a specific wiki page."""
        request = ado_client.session.get(
            f"https://dev.azure.com/{ado_client.ado_org_name}/{ado_client.ado_project_name}/_apis/wiki/wikis/{wiki_id}/pages?path={wiki_page_path}&recursionLevel=1&versionDescriptor.version=wikiMaster"
        )
        return request.json()  # type: ignore[no-any-return]

    @classmethod
    def get_all_pages_contents(cls, ado_client: "AdoClient", wiki_id: str, path: str = "/", precached_list_of_paths: list[str] | None = None) -> dict[str, str]:
        return {
            page_path: cls.download_page_contents(ado_client, wiki_id, page_path)
            for page_path in precached_list_of_paths or cls.get_all_paths(ado_client, wiki_id, path)
        }

    @classmethod
    def get_all_pages_contents_generator(cls, ado_client: "AdoClient", wiki_id: str, path: str = "/", precached_list_of_paths: list[str] | None = None) -> Generator[tuple[str, str], None, None]:
        list_of_paths = precached_list_of_paths if precached_list_of_paths else cls.get_all_paths(ado_client, wiki_id, path)
        for page_path in list_of_paths:
            yield (page_path, cls.download_page_contents(ado_client, wiki_id, page_path))

    @classmethod
    def get_all_paths_with_metadata(
        cls, ado_client: "AdoClient", wiki_id: str, path: str = "/"
    ) -> dict[str, dict[str, Any]]:
        """Fetches all pages in a given wiki, handling API pagination and returning metadata."""
        # TODO: Test and develop this.
        all_pages: dict[str, dict[str, Any]] = {}
        request = ado_client.session.get(
            f"https://dev.azure.com/{ado_client.ado_org_name}/{ado_client.ado_project_name}/_apis/wiki/wikis/{wiki_id}/pages?path={path}&recursionLevel=1&versionDescriptor.version=wikiMaster"
        )
        data = request.json()
        for page in data.get("subPages", []):
            if page.get("isParentPage"):
                all_pages |= cls.get_all_paths_with_metadata(ado_client, wiki_id, page["path"])
            all_pages[page["path"]] = cls.get_page_metadata(ado_client, wiki_id, page["path"])
        return all_pages

    @classmethod
    def get_all_paths(cls, ado_client: "AdoClient", wiki_id: str, path: str = "/") -> list["str"]:
        """Fetches all pages in a given wiki, handling API pagination."""
        all_page_paths: list[str] = []
        request = ado_client.session.get(
            f"https://dev.azure.com/{ado_client.ado_org_name}/{ado_client.ado_project_name}/_apis/wiki/wikis/{wiki_id}/pages?path={path}&recursionLevel=1&versionDescriptor.version=wikiMaster"
        )
        data = request.json()
        for page in data.get("subPages", []):
            if page.get("isParentPage"):
                all_page_paths.extend(cls.get_all_paths(ado_client, wiki_id, page["path"]))
            all_page_paths.append(page["path"])

        return all_page_paths
