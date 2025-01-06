from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Literal

from ado_wrapper.errors import UnknownError
from ado_wrapper.state_managed_abc import convert_from_json
from ado_wrapper.utils import ANSI_GREEN, ANSI_RED, ANSI_RESET, ANSI_MAGENTA, build_hierarchy_payload, requires_initialisation

if TYPE_CHECKING:
    from ado_wrapper.client import AdoClient

CommitChangeType = Literal["add", "edit", "delete", "rename", "rename_and_edit"]
change_type_mapping: dict[int, CommitChangeType] = {1: "add", 2: "delete", 3: "edit"}
FIRST_COMMIT_ID = "0000000000000000000000000000000000000000"


# ====================================================================================================================


@dataclass
class ChangedFile:
    blocks: list["SurroundingContext | Padding | CommitChange"]
    old_file_name: str | None = None
    new_file_name: str | None = None

    def __str__(self) -> str:
        string = ""
        if self.old_file_name is not None:
            string += f"{ANSI_MAGENTA}ChangedFile(old_file_name={self.old_file_name}, new_file_name={self.new_file_name}){ANSI_RESET}"
        if self.blocks:
            string += "\n" + "\n".join([str(block) for block in self.blocks])
        return string

    @staticmethod
    def to_string(changed_files: dict[str, "ChangedFile"]) -> str:
        string = ""
        for file_name, changed_file in changed_files.items():
            string += f"\n{file_name}:\n{'='*50}\n{changed_file}\n"
        return string

    @staticmethod
    def dict_to_type(data: dict[str, Any]) -> "SurroundingContext | Padding | CommitChange":
        mapping: dict[str, type[Padding] | type[SurroundingContext] | type[CommitChange]] = {
            "Padding": Padding, "SurroundingContext": SurroundingContext, "CommitChange": CommitChange
        }
        return mapping[data["item_type"]].from_json(data)

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> "ChangedFile":
        return cls([cls.dict_to_type(item) for item in data["blocks"]], data.get("old_file_name"), data.get("new_file_name"))

    def to_json(self) -> dict[str, Any]:
        dictionary: dict[str, Any] = {"blocks": [x.to_json() for x in self.blocks]}
        if self.old_file_name is not None:
            dictionary["old_file_name"] = self.old_file_name
        if self.new_file_name is not None:
            dictionary["new_file_name"] = self.new_file_name
        return dictionary

    @classmethod
    def get_changed_file(
        cls, ado_client: "AdoClient", repo_id: str, old_file_path: str | None, new_file_path: str, change_type: CommitChangeType, change_commit_id: str, old_commit_id: str
    ) -> "ChangedFile":  # fmt: skip
        if change_type == "rename":
            return ChangedFile([], old_file_path, new_file_path)
        PAYLOAD = build_hierarchy_payload(
            ado_client, "code-web.file-diff-data-provider", additional_properties={
                "diffParameters": {
                    "includeCharDiffs": True, "partialDiff": True, "forceLoad": False,
                    "modifiedVersion": "GC"+change_commit_id, "modifiedPath": new_file_path if change_type != "delete" else "",
                    "originalVersion": "GC"+old_commit_id, "originalPath": (old_file_path or new_file_path) if change_type != "add" else "",
                },
                "repositoryId": repo_id,
            }  # fmt: skip
        )
        # print("MINE=", PAYLOAD["dataProviderContext"]["properties"]["diffParameters"])
        request = ado_client.session.post(
            f"https://dev.azure.com/{ado_client.ado_org_name}/_apis/Contribution/HierarchyQuery/project/{ado_client.ado_project_id}?api-version=7.1-preview.1",
            json=PAYLOAD,
        ).json()["dataProviders"]
        if "ms.vss-code-web.file-diff-data-provider" not in request:
            print(f'"{old_file_path}", "{new_file_path}", "{change_type}", "{change_commit_id}", "{old_commit_id}"')
            raise UnknownError(f"Error, could not fetch file changes for {new_file_path}!")
        data = request["ms.vss-code-web.file-diff-data-provider"]
        if "lineCharBlocks" not in data:  # Binary files + Images cannot be seen as text
            if data.get("modifiedFile", {}).get("contentMetadata", {}).get("isBinary", False):
                file_extension = data["modifiedFile"]["contentMetadata"]["extension"]
            else:
                file_extension = data["originalFile"]["serverItem"].split(".")[-1]
            content = f"This file contains non-printable characters and no other viewer was found for file extension \"{file_extension}\"."
            return ChangedFile(blocks=[SurroundingContext("SurroundingContext", [content])])
        blocks: list[Padding | SurroundingContext | CommitChange] = []
        for block in [x["lineChange"] for x in data["lineCharBlocks"]]:
            if block.get("truncatedBefore") and not (blocks and isinstance(blocks[-1], Padding)):  # Don't double up on Padding
                blocks.append(Padding())
            elif block["changeType"] == 0:
                blocks.append(SurroundingContext("SurroundingContext", block["mLines"], block["mLine"]))
            elif block["changeType"] in change_type_mapping:
                commit_change = CommitChange.from_request_payload(block)
                blocks.append(commit_change)
            elif block.get("truncatedAfter") and not isinstance(blocks[-1], Padding):  # Don't double up on Padding
                blocks.append(Padding())
            else:
                print(f"Could not place {block}")
        return ChangedFile(blocks)

    @classmethod
    def get_changed_content(cls, ado_client: "AdoClient", repo_id: str, commit_id: str, branch_name: str = "main") -> dict[str, "ChangedFile"]:
        """Only used by commits, PRs do some additional process and use cls.get_changed_file on all of them."""
        requires_initialisation(ado_client)
        # ========================================================================================================================
        # Get affected files:
        changes_request = ado_client.session.post(
            f"https://dev.azure.com/{ado_client.ado_org_name}/{ado_client.ado_project_name}/_git/{repo_id}/commit/{commit_id}?refName=refs/heads/{branch_name}&__rt=fps&__ver=2"
        ).json()["fps"]["dataProviders"]["data"]["ms.vss-code-web.commit-details-view-data-provider"]["commitDetails"]
        old_commit_id = changes_request["parents"][0] if changes_request["parents"] else FIRST_COMMIT_ID
        mapping: dict[int, CommitChangeType] = {1: "add", 2: "edit", 8: "rename", 10: "rename", 16: "delete"}  # sourceRename, undelete
        # 1040: "rename_and_edit"  <- This is actually a duplicate entry, which will exist as well as the 10: "rename" entry...
        affected_files: list[tuple[str | None, str, CommitChangeType, str]] = [
            (
                x.get("sourceServerItem"),  # None | old path/file name
                x["item"]["path"],  # (New) Path
                mapping[x["changeType"]],  # Change type, e.g. add, remove
                x["item"]["commitId"],  # Modified Commit id
            )
            for x in changes_request["changes"]
            if x["item"]["gitObjectType"] == 3  # 2 = Folder (tree internally), 3 = File (blob internally)
            and x["changeType"] != 1040
        ]  # fmt: skip
        # ========================================================================================================================
        # And each affected file.
        changed_files: dict[str, ChangedFile] = {
            new_file_path: cls.get_changed_file(ado_client, repo_id, old_file_path, new_file_path, change_type, change_commit_id, old_commit_id)
            for old_file_path, new_file_path, change_type, change_commit_id in affected_files
        }
        return changed_files

# ====================================================================================================================


@dataclass
class Padding:
    item_type: str = field(repr=False, default="Padding")

    def __str__(self) -> str:
        return "\n"+"-"*100+"\n"

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> "Padding":
        del data["item_type"]
        return Padding(**data)

    def to_json(self) -> dict[str, Any]:
        return {"item_type": self.item_type}


# ====================================================================================================================


@dataclass
class SurroundingContext:
    item_type: str = field(repr=False)
    content: list[str] = field(repr=False)
    starting_line: int = field(repr=False, default=0)

    def __str__(self) -> str:
        line_num = self.starting_line
        string = ""
        for line in self.content:
            string += f"{line_num:>3}    {line}\n"
            line_num += 1
        return string.rstrip("\n")

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> "SurroundingContext":
        del data["item_type"]
        return cls(item_type="SurroundingContext", **convert_from_json(data))

    def to_json(self) -> dict[str, Any]:
        return {"item_type": self.item_type, "content": self.content, "starting_line": self.starting_line}


# ====================================================================================================================


@dataclass
class CommitChange:
    item_type: str = field(repr=False)
    change_type: CommitChangeType
    previous_line_number: int = field(repr=False)
    new_line_number: int = field(repr=False)
    previous_lines: list[str] = field(repr=False)
    new_lines: list[str] = field(repr=False)

    @classmethod
    def from_request_payload(cls, data: dict[str, Any]) -> "CommitChange":
        return cls(cls.__name__, change_type_mapping[data["changeType"]], data["oLine"], data["mLine"], data.get("oLines", []), data.get("mLines", []))

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> "CommitChange":
        del data["item_type"]
        return cls(cls.__name__, **data)

    def to_json(self) -> dict[str, Any]:
        return {
            "item_type": self.__class__.__name__,
            "change_type": self.change_type, "previous_line_number": self.previous_line_number,
            "new_line_number": self.new_line_number, "previous_lines": self.previous_lines,
            "new_lines": self.new_lines,
        }  # fmt: skip

    @staticmethod
    def padded_line_count(number: int, colour: str, char: str, line: str) -> str:
        return f"{number:>3}  {colour}{char} {line}{ANSI_RESET}\n"

    def __str__(self) -> str:
        string = ""
        if self.change_type in ["add", "delete"]:
            colour = ANSI_GREEN if self.change_type == "add" else ANSI_RED
            symbol = "+" if self.change_type == "add" else "-"
            lines = self.new_lines if self.change_type == "add" else self.previous_lines
            for i, line in enumerate(lines):
                string += self.padded_line_count(i+self.new_line_number, colour, symbol, line)
        elif self.change_type == "edit":
            for i, (old_line, new_line) in enumerate(zip(self.previous_lines, self.new_lines)):
                string += self.padded_line_count(i+self.new_line_number, ANSI_RED, '-', old_line)
                string += self.padded_line_count(i+self.new_line_number, ANSI_GREEN, '+', new_line)
        return string.rstrip("\n")
