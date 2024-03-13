from __future__ import annotations

import io
import zipfile
import requests

from typing import TYPE_CHECKING

from pull_requests import PullRequest, PullRequestStatus

if TYPE_CHECKING:
    from client import AdoClient


class Repo:
    def __init__(self, repo_id: str, name: str) -> None:
        self.repo_id = repo_id
        self.name = name

    def __repr__(self) -> str:
        return f"Repo(name={self.name}, id={self.repo_id})"

    def __str__(self) -> str:
        return f"Repo(name={self.name}, id={self.repo_id})"

    @classmethod
    def from_json(cls, repo_response: dict[str, str]) -> "Repo":
        return cls(repo_response["id"], repo_response["name"])

    @classmethod
    def create(cls, ado_client: AdoClient, name: str) -> "Repo":
        request = requests.post(
            f"https://dev.azure.com/{ado_client.ado_org}/{ado_client.ado_project}/_apis/git/repositories?api-version=6.0",
            json={"name": name},
            auth=ado_client.auth,
        ).json()
        return cls.from_json(request)

    @classmethod
    def get_all(cls, ado_client: AdoClient) -> list["Repo"]:
        request = requests.get(
            f"https://dev.azure.com/{ado_client.ado_org}/{ado_client.ado_project}/_apis/git/repositories?api-version=7.1",
            auth=ado_client.auth,
        ).json()
        return [cls.from_json(repo) for repo in request["value"]]

    @classmethod
    def get_by_name(cls, ado_client: AdoClient, repo_name: str) -> "Repo":
        """Warning, this function must fetch `all` repos to work, be cautious when calling it in a loop."""
        request = requests.get(
            f"https://dev.azure.com/{ado_client.ado_org}/{ado_client.ado_project}/_apis/git/repositories?api-version=7.1",
            auth=ado_client.auth,
        ).json()
        for repo in request["value"]:
            if repo["name"] == repo_name:
                return cls.from_json(repo)
        raise ValueError(f"Repo {repo_name} not found")

    @classmethod
    def get_by_id(cls, ado_client: AdoClient, repo_id: str) -> "Repo":
        request = requests.get(f"https://dev.azure.com/{ado_client.ado_org}/{ado_client.ado_project}/_apis/git/repositories/{repo_id}?api-version=7.1", auth=ado_client.auth).json()  # fmt: skip
        return cls.from_json(request)

    def get_file(self, ado_client: AdoClient, file_path: str) -> str:
        request = requests.get(f"https://dev.azure.com/{ado_client.ado_org}/{ado_client.ado_project}/_apis/git/repositories/{self.repo_id}/items?path={file_path}&api-version=7.1", auth=ado_client.auth)  # fmt: skip
        if request.status_code == 404:
            raise FileNotFoundError(f"File {file_path} not found in repo {self.repo_id}")
        if request.status_code != 200:
            raise Exception(f"Error getting file {file_path} from repo {self.repo_id}: {request.text}")
        return request.text  # This is the file content

    def get_repo_contents(self, ado_client: AdoClient, file_types: list[str] | None = None) -> dict[str, str]:
        """This function downloads the contents of a repo, and returns a dictionary of the files and their contents
        The file_types parameter is a list of file types to filter for, e.g. ["json", "yaml"]"""
        try:
            request = requests.get(
                f"https://dev.azure.com/{ado_client.ado_org}/{ado_client.ado_project}/_apis/git/repositories/{self.repo_id}/items?recursionLevel=Full&download=true&$format=Zip&api-version=6.0",
                auth=ado_client.auth,
            )
        except requests.exceptions.ConnectionError:
            print(f"=== Connection error, failed to download {self.repo_id}")
        # ============ We do this because ADO ===================
        bytes_io = io.BytesIO()
        for chunk in request.iter_content(chunk_size=128):
            bytes_io.write(chunk)

        files = {}
        try:
            with zipfile.ZipFile(bytes_io) as zip_ref:
                # For each file, read the bytes and convert to string
                for file_name in [x for x in zip_ref.namelist() if file_types is None or x.split(".")[-1] in file_types]:
                    files[file_name] = zip_ref.read(file_name).decode()  # fmt: skip
        except zipfile.BadZipFile as e:
            print(f"{self.repo_id} couldn't be unzipped:", e)

        bytes_io.close()
        # =========== That's all I have to say ==================
        return files

    def create_pull_request(
        self, ado_client: AdoClient, branch_name: str, pull_request_title: str, pull_request_description: str
    ) -> "PullRequest":
        """Helper function which redirects to the PullRequest class and makes a PR"""
        return PullRequest.create(ado_client, self.repo_id, branch_name, pull_request_title, pull_request_description)

    def get_all_pull_requests(self, ado_client: AdoClient, status: PullRequestStatus) -> list["PullRequest"]:
        pull_requests = requests.get(
            f"https://dev.azure.com/{ado_client.ado_org}/{ado_client.ado_project}/_apis/git/repositories/{self.repo_id}/pullrequests?searchCriteria.status={status}&api-version=7.1",
            auth=ado_client.auth,
        ).json()
        try:
            return [PullRequest.from_json(pr) for pr in pull_requests["value"]]
        except KeyError:
            if pull_requests["message"].startswith("TF401019"):
                print(f"Repo {pull_requests['message'].split('identifier')[1].split(' ')[0]} was disabled, or you had no access.")
            return []

    def delete(self, ado_client: AdoClient) -> None:
        request = requests.delete(f"https://dev.azure.com/{ado_client.ado_org}/{ado_client.ado_project}/_apis/git/repositories/{self.repo_id}?api-version=7.1", auth=ado_client.auth)  # fmt: skip
        assert request.status_code == 204


if __name__ == "__main__":
    from secret import email, ado_access_token, ado_org, ado_project, ALTERNATIVE_EXISTING_REPO_NAME
    from client import AdoClient

    ado_client = AdoClient(email, ado_access_token, ado_org, ado_project)
    repo = Repo.get_by_name(ado_client, ALTERNATIVE_EXISTING_REPO_NAME)
    print(repo)
