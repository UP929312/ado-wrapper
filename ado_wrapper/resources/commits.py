from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Any, Literal

from ado_wrapper.resources.users import Member
from ado_wrapper.state_managed_abc import StateManagedResource
from ado_wrapper.errors import ConfigurationError, InvalidPermissionsError  # , UnknownError
from ado_wrapper.utils import from_ado_date_string

# from ado_wrapper.resources.branches import Branch

if TYPE_CHECKING:
    from ado_wrapper.client import AdoClient

CommitChangeType = Literal["edit", "add", "delete"]
FIRST_COMMIT_ID = "0000000000000000000000000000000000000000"  # This is the initial id

GitIgnoreTemplateType = Literal[
    'Actionscript', 'Ada', 'Agda', 'Android', 'AppceleratorTitanium', 'AppEngine', 'ArchLinuxPackages', 'Autotools', 'C++', 'C',
    'CakePHP', 'CFWheels', 'ChefCookbook', 'Clojure', 'CMake', 'CodeIgniter', 'CommonLisp', 'Composer', 'Concrete5', 'Coq', 'CraftCMS',
    'CUDA', 'D', 'Dart', 'Delphi', 'DM', 'Drupal', 'Eagle', 'Elisp', 'Elixir', 'Elm', 'EPiServer', 'Erlang', 'ExpressionEngine', 'ExtJs',
    'Fancy', 'Finale', 'ForceDotCom', 'Fortran', 'FuelPHP', 'gcov', 'GitBook', 'Go', 'Godot', 'Gradle', 'Grails', 'GWT', 'Haskell',
    'Idris', 'IGORPro', 'Java', 'Jboss', 'Jekyll', 'JENKINS_HOME', 'Joomla', 'Julia', 'KiCAD', 'Kohana', 'Kotlin', 'LabVIEW', 'Laravel',
    'Leiningen', 'LemonStand', 'Lilypond', 'Lithium', 'Lua', 'Magento', 'Maven', 'Mercury', 'MetaProgrammingSystem', 'nanoc', 'Nim', 'Node',
    'Objective-C', 'OCaml', 'Opa', 'opencart', 'OracleForms', 'Packer', 'Perl', 'Phalcon', 'PlayFramework', 'Plone', 'Prestashop', 'Processing',
    'PureScript', 'Python', 'Qooxdoo', 'Qt', 'R', 'Rails', 'Raku', 'RhodesRhomobile', 'ROS', 'Ruby', 'Rust', 'Sass', 'Scala', 'Scheme', 'SCons',
    'Scrivener', 'Sdcc', 'SeamGen', 'SketchUp', 'Smalltalk', 'stella', 'SugarCRM', 'Swift', 'Symfony', 'SymphonyCMS', 'Terraform', 'TeX',
    'Textpattern', 'TurboGears2', 'Typo3', 'Umbraco', 'Unity', 'UnrealEngine', 'VisualStudio', 'VVVV', 'Waf', 'WordPress', 'Xojo', 'Yeoman',
    'Yii', 'ZendFramework', 'Zephir'  # fmt: skip
]
README_PAYLOAD = {"changeType": 1, "item": {"path": "/README.md"}, "newContentTemplate": {"name": "README.md", "type": "readme"}}


def get_commit_body_template(
    old_object_id: str | None, updates: dict[str, str], branch_name: str, change_type: CommitChangeType, commit_message: str
) -> dict[str, Any]:  # fmt: skip
    return {
        "refUpdates": [
            {
                "name": f"refs/heads/{branch_name}",
                "oldObjectId": old_object_id or FIRST_COMMIT_ID,
            },
        ],
        "commits": [
            {
                "comment": commit_message,
                "changes": [
                    {
                        "changeType": change_type,
                        "item": {
                            "path": path,
                        },
                        "newContent": {
                            "content": new_content_body,
                            "contentType": "rawtext",
                        },
                    }
                    for path, new_content_body in updates.items()
                ],
            }
        ],
    }


@dataclass
class Commit(StateManagedResource):
    """
    https://learn.microsoft.com/en-us/rest/api/azure/devops/git/commits?view=azure-devops-rest-7.1
    https://learn.microsoft.com/en-us/rest/api/azure/devops/git/pushes?view=azure-devops-rest-7.1
    """

    commit_id: str = field(metadata={"is_id_field": True})  # None are editable
    author: Member
    date: datetime
    message: str
    repo_id: str

    def __str__(self) -> str:
        return f"{self.commit_id} by {self.author!s} on {self.date}\n{self.message}"

    @classmethod
    def from_request_payload(cls, data: dict[str, Any]) -> "Commit":
        repo_id = data["url"].split("_apis/git/repositories/")[1].split("/commits/")[0]
        member = Member(data["author"]["name"], data["author"].get("email", "BOT USER"), "UNKNOWN")
        return cls(data["commitId"], member, from_ado_date_string(data["author"]["date"]), data["comment"], repo_id)

    @classmethod
    def get_by_id(cls, ado_client: "AdoClient", repo_id: str, commit_id: str) -> "Commit":
        return super()._get_by_url(
            ado_client,
            f"/{ado_client.ado_project_name}/_apis/git/repositories/{repo_id}/commits/{commit_id}?api-version=7.1",
        )

    @classmethod
    def create(
        cls, ado_client: "AdoClient", repo_id: str, from_branch_name: str, to_branch_name: str,
        updates: dict[str, str], change_type: CommitChangeType = "add", commit_message: str = "New Commit",  # fmt: skip
    ) -> "Commit":
        """Creates a commit in the given repository with the given updates and returns the commit object.
        Takes a branch to get the latest commit from (and to update), and a to_branch to fork to."""
        if from_branch_name.startswith("refs/heads/") or to_branch_name.startswith("refs/heads/"):
            raise ConfigurationError("Branch names should not start with 'refs/heads/'")
        #
        # existing_branches = Branch.get_all_by_repo(ado_client, repo_id)
        # if to_branch_name not in [x.name for x in existing_branches]:
        #     ado_client.state_manager.add_resource_to_state("Branch", to_branch_name, {})
        #
        if not updates:
            raise ValueError("No updates provided! It's not possible to create a commit without updates.")
        latest_commit = cls.get_latest_by_repo(ado_client, repo_id, from_branch_name)
        latest_commit_id = None if latest_commit is None else latest_commit.commit_id
        data = get_commit_body_template(latest_commit_id, updates, to_branch_name, change_type, commit_message)
        request = ado_client.session.post(
            f"https://dev.azure.com/{ado_client.ado_org_name}/{ado_client.ado_project_name}/_apis/git/repositories/{repo_id}/pushes?api-version=7.1",
            json=data,
        )
        if request.status_code == 400:
            raise ValueError("The commit was not created successfully, the file(s) you're trying to add might already exist there.")
        if request.status_code == 403:
            raise InvalidPermissionsError("You do not have permission to create a commit in this repo (possibly due to main branch protections)")  # fmt: skip
        if not request.json().get("commits"):
            raise ValueError("The commit was not created successfully.\nError:", request.json())
        return cls.from_request_payload(request.json()["commits"][-1])

    @staticmethod
    def delete_by_id(ado_client: "AdoClient", commit_id: str) -> None:
        raise NotImplementedError

    def link(self, ado_client: "AdoClient") -> str:
        return f"https://dev.azure.com/V{ado_client.ado_org_name}/{ado_client.ado_project_name}/_git/{self.repo_id}/commit/{self.commit_id}"

    # ============ End of requirement set by all state managed resources ================== #
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
    # =============== Start of additional methods included with class ===================== #

    @classmethod
    def get_latest_by_repo(cls, ado_client: "AdoClient", repo_id: str, branch_name: str | None = None) -> "Commit":
        return max(cls.get_all_by_repo(ado_client, repo_id, branch_name), key=lambda commit: commit.date)

    @classmethod
    def get_all_by_repo(cls, ado_client: "AdoClient", repo_id: str, branch_name: str | None = None) -> "list[Commit]":
        """Returns a list of all commits in the given repository."""
        extra_query = (f"searchCriteria.itemVersion.version={branch_name}&searchCriteria.itemVersion.versionType={'branch'}&"
                       if branch_name is not None else "")  # fmt: skip
        return super()._get_all(
            ado_client,
            f"/{ado_client.ado_project_name}/_apis/git/repositories/{repo_id}/commits?{extra_query}api-version=7.1",
        )  # pyright: ignore[reportReturnType]

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #

    @classmethod
    def add_initial_readme(cls, ado_client: "AdoClient", repo_id: str) -> "Commit":
        default_commit_body = get_commit_body_template(None, {}, "main", "add", "")
        default_commit_body["commits"] = [{"comment": "Add README.md", "changes": [README_PAYLOAD]}]  # fmt: skip
        request = ado_client.session.post(
            f"https://dev.azure.com/{ado_client.ado_org_name}/{ado_client.ado_project_name}/_apis/git/repositories/{repo_id}/pushes?api-version=7.1",
            json=default_commit_body,
        ).json()
        return cls.from_request_payload(request["commits"][0])

    @classmethod
    def add_git_ignore_template(cls, ado_client: "AdoClient", repo_id: str, git_ignore_template: GitIgnoreTemplateType) -> "Commit":
        default_commit_body = get_commit_body_template(None, {}, "main", "add", "")
        default_commit_body["commits"] = [{
            "comment": f"Added .gitignore ({git_ignore_template})",
            "changes": [{
                "changeType": 1, "item": {"path": "/.gitignore"},
                "newContentTemplate": {"name": f"{git_ignore_template}.gitignore", "type": "gitignore"}
            }],
        }]  # fmt: skip
        request = ado_client.session.post(
            f"https://dev.azure.com/{ado_client.ado_org_name}/{ado_client.ado_project_name}/_apis/git/repositories/{repo_id}/pushes?api-version=7.1",
            json=default_commit_body,
        ).json()
        return cls.from_request_payload(request["commits"][0])

    @classmethod
    def add_readme_and_gitignore(cls, ado_client: "AdoClient", repo_id: str, git_ignore_template: GitIgnoreTemplateType) -> "Commit":
        default_commit_body = get_commit_body_template(None, {}, "main", "add", "")
        default_commit_body["commits"] = [{
            "comment": f"Added README.md, .gitignore ({git_ignore_template}) files",
            "changes": [
                README_PAYLOAD,
                {
                    "changeType": 1, "item": {"path": "/.gitignore"},
                    "newContentTemplate": {"name": f"{git_ignore_template}.gitignore", "type": "gitignore"}
                },
            ],
        }]  # fmt: skip
        request = ado_client.session.post(
            f"https://dev.azure.com/{ado_client.ado_org_name}/{ado_client.ado_project_name}/_apis/git/repositories/{repo_id}/pushes?api-version=7.1",
            json=default_commit_body,
        ).json()
        return cls.from_request_payload(request["commits"][0])

    # @classmethod
    # def roll_back_latest_commit(cls, ado_client: "AdoClient", repo_id: str, branch_name: str) -> None:
    #     from ado_wrapper.resources.repo import Repo

    #     latest_commit = Commit.get_latest_by_repo(ado_client, repo_id, branch_name)
    #     repo_name = Repo.get_by_id(ado_client, repo_id).name
    #     generated_ref_name = f"refs/heads/{latest_commit}[:8]-revert-from-{branch_name}"
    #     PAYLOAD = {
    #         "generatedRefName": generated_ref_name,
    #         "ontoRefName": f"refs/heads/{branch_name}",
    #         "source": {"commitList": [{"commitId": latest_commit}]},
    #         "repository": {
    #             "id": repo_id,
    #             "name": repo_name,
    #             "project": {"id": ado_client.ado_project_id, "name": ado_client.ado_project_name, "state": 1, "revision":399,
    #                         "visibility":0,"lastUpdateTime":"2024-02-06T14:14:30.360Z"},
    #             },
    #         },
    #     pr_ref_request = ado_client.session.post(
    #         f"https://dev.azure.com/{ado_client.ado_org_name}/{ado_client.ado_project_id}/_apis/git/repositories/{repo_id}/reverts",
    #         json=PAYLOAD
    #     )
    #     if pr_ref_request.status_code != 201:
    #         raise UnknownError(f"Could not rollback commit pull request reference. Error: {pr_ref_request.text}")
    #     # CREATE THE PULL REQUEST REF ^
    #     ## =======
    #     extra_params = {
    #         "sourceRef": generated_ref_name,
    #         "targetRef": branch_name,
    #         "sourceRepositoryId": repo_id,
    #         "targetRepositoryId": repo_id,
    #         "revertCommit": latest_commit.commit_id,
    #         "__rt": "fps",
    #         "__ver": 2,
    #     }
    #     pull_request_create_request = ado_client.session.post(
    #         f"https://dev.azure.com/{ado_client.ado_org_name}/{ado_client.ado_project_name}/_git/{repo_name}/pullrequestcreate?api-version=7.1-preview.1&{'&'.join(extra_params)}",
    #     )
    #     if pull_request_create_request.status_code != 201:
    #         raise UnknownError(f"Could not rollback commit pull request. Error: {pull_request_create_request.text}")
    #     # ====
    #     PAYLOAD = {"description":"Revert \"Test commit 3\"\n\nReverted commit `a2a177ea`.","isDraft": False,"labels":[],"reviewers":[],"sourceRefName":"refs/heads/a2a177e3-revert-from-new-branch","targetRefName":"refs/heads/new-branch","title":"Revert \"Test commit 3\""}
    #     accept_create_pr_request = ado_client.session.post(
    #         f"https://dev.azure.com/benskerritt/cc1e50e7-580c-43bc-8589-1e4d134ad61b/_apis/git/repositories/16db8bc8-4956-4748-b845-d1f41ded2640/pullRequests?supportsIterations=true",
    #         json=PAYLOAD,
    # )
    # revert_get_request = ado_client.session.get(
    #     f"https://dev.azure.com/{ado_client.ado_org_name}/{ado_client.ado_project_id}/_apis/git/repositories/{repo_id}/reverts/{request.json()['revertId']}"
    # ).json()
    # if revert_get_request["status"] == 4 or revert_get_request["detailedStatus"]["conflict"]:
    #     raise UnknownError("Error, there was a detected conflict and therefore could not complete.")
