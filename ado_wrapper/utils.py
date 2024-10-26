import re
from dataclasses import fields
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Literal, TypeVar, ParamSpec, overload, Any, Type, Generic

from ado_wrapper.errors import ConfigurationError

if TYPE_CHECKING:
    from ado_wrapper.client import AdoClient
    from ado_wrapper.state_managed_abc import StateManagedResource

T = TypeVar("T")
P = ParamSpec("P")

ANSI_RE_PATTERN = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
DATETIME_RE_PATTERN = re.compile(r"^20\d\d-\d\d-\d\dT\d\d:\d\d:\d\d\.\d{7}Z")

ANSI_GREY = "\x1B[90m"
ANSI_GRAY = ANSI_GREY

ANSI_WHITE = "\x1B[37m"
ANSI_CYAN = "\x1B[36m"
ANSI_MAGENTA = "\x1B[35m"
ANSI_BLUE = "\x1B[34m"
ANSI_YELLOW = "\x1B[33m"
ANSI_GREEN = "\x1B[32m"
ANSI_RED = "\x1B[31m"
ANSI_BLACK = "\x1B[30m"

ANSI_UNDERLINE = "\x1b[4m"
ANSI_BOLD = "\x1B[1m"
ANSI_RESET = "\x1B[0m"


def remove_ansi_codes(string: str) -> str:
    return ANSI_RE_PATTERN.sub("", string)


@overload
def from_ado_date_string(date_string: str) -> datetime:
    ...


@overload
def from_ado_date_string(date_string: None) -> None:
    ...


def from_ado_date_string(date_string: str | None) -> datetime | None:
    if date_string is None:
        return None
    if date_string.startswith("/Date("):
        return datetime.fromtimestamp(int(date_string[6:-2]) / 1000, tz=timezone.utc)
    no_milliseconds = date_string.split(".")[0].removesuffix("Z")
    return datetime.strptime(no_milliseconds, "%Y-%m-%dT%H:%M:%S")


@overload
def to_iso(dt: datetime) -> str:
    ...


@overload
def to_iso(dt: None) -> None:
    ...


def to_iso(dt: datetime | None) -> str | None:
    if dt is None:
        return None
    return datetime.isoformat(dt)


@overload
def from_iso(dt_string: str) -> datetime:
    ...


@overload
def from_iso(dt_string: None) -> None:
    ...


def from_iso(dt_string: str | None) -> datetime | None:
    if dt_string is None:
        return None
    dt = datetime.fromisoformat(dt_string)
    return dt.replace(tzinfo=timezone.utc)


def get_fields_metadata(cls: type["StateManagedResource"]) -> dict[str, dict[str, str]]:
    return {field_obj.name: dict(field_obj.metadata) for field_obj in fields(cls)}


def get_id_field_name(cls: type["StateManagedResource"]) -> str:
    """Returns the name of the field that is marked as the id field. If no id field is found, a ValueError is raised."""
    for field_name, metadata in get_fields_metadata(cls).items():
        if metadata.get("is_id_field", False):
            return field_name
    raise ValueError(f"No id field found for {cls.__name__}!")


def extract_id(obj: "StateManagedResource") -> str:
    """Extracts the id from a StateManagedResource object. The id field is defined by the "is_id_field" metadata."""
    id_field_name = get_id_field_name(obj.__class__)
    return str(getattr(obj, id_field_name))


def get_editable_fields(cls: type["StateManagedResource"]) -> list[str]:
    """Returns a list of attribute that are marked as editable."""
    return [field_obj.name for field_obj in cls.__dataclass_fields__.values() if field_obj.metadata.get("editable", False)]


def get_internal_field_names(
    cls: type["StateManagedResource"], field_names: list[str] | None = None, reverse: bool = False
) -> dict[str, str]:  # fmt: skip
    """Returns a mapping of field names to their internal names. If no internal name is set, the field name is used."""
    if field_names is None:
        field_names = get_editable_fields(cls)
    value = {field_name: cls.__dataclass_fields__[field_name].metadata.get("internal_name", field_name) for field_name in field_names}
    if reverse:
        return {v: k for k, v in value.items()}
    return value


def requires_initialisation(ado_client: "AdoClient") -> None:
    """Certain services/endpoints require the ado_project_id, which isn't set if bypass_initialisation is set to False."""
    if not ado_client.ado_project_id:
        raise ConfigurationError(
            "The client has not been initialised. Please disable `bypass_initialisation` in AdoClient before using this function."
        )


def recursively_find_or_none(data: dict[str, Any], indexes: list[str]) -> Any:
    current = data
    for index in indexes:
        if index not in current:
            return None
        current = current[index]
    return current


def build_hierarchy_payload(
    ado_client: "AdoClient", contribution_id: str, route_id: str | None = None, additional_properties: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Additional properties are put into `dataProviderContext/properties`"""
    requires_initialisation(ado_client)
    data: dict[str, Any] = {"dataProviderContext": {"properties": {"sourcePage": {"routeValues": {}}}}}
    if additional_properties:
        data["dataProviderContext"]["properties"] |= additional_properties
    if route_id:
        data["dataProviderContext"]["properties"]["sourcePage"]["routeId"] = f"ms.vss-{route_id}"
    data["contributionIds"] = [f"ms.vss-{contribution_id}"]
    data["dataProviderContext"]["properties"]["sourcePage"]["routeValues"]["projectId"] = ado_client.ado_project_id
    data["dataProviderContext"]["properties"]["sourcePage"]["routeValues"]["project"] = ado_client.ado_project_name
    return data


# def requires_perms(required_perms: list[str] | str) -> Callable[[Callable[P, T]], Callable[P, T]]:
#     """This wraps a call (with ado_client as second arg) with a list of required permissions,
#     will raise an error if the client doesn't have them"""

#     def decorator(func: Callable[P, T]) -> Callable[P, T]:
#         def wrapper(cls: Type[Any], ado_client: "AdoClient", *args: P.args, **kwargs: P.kwargs) -> T:
#             if ado_client.perms is not None:
#                 for required_perm_name in required_perms if isinstance(required_perms, list) else [required_perms]:
#                     if required_perm_name not in [f"{x.group}/{x.name}" for x in ado_client.perms if x.has_permission]:
#                         raise InvalidPermissionsError(f"Error! The client tried to make a call to a service with invalid permissions! Didn't have {required_perm_name}")  # fmt: skip
#             elif not ado_client.suppress_warnings:
#                 print("[ADO_WRAPPER] Warning, could not verify the authenticated PAT has the right perms.")
#             return func(cls, ado_client, *args, **kwargs)  # type: ignore[arg-type]

#         return wrapper  # type: ignore[return-value]

#     return decorator


class TemporaryResource(Generic[T]):
    """A context manager which creates and (always) deletes a resource"""

    def __init__(self, ado_client: "AdoClient", cls: Type[T], *args, **kwargs):  # type: ignore[no-untyped-def]
        self.ado_client = ado_client
        self.cls = cls
        self.args = args
        self.delete_after = True
        if "delete_after" in kwargs:
            self.delete_after = kwargs.pop("delete_after")
        self.kwargs = kwargs

    def __enter__(self) -> T:
        self.resource: T = self.cls.create(self.ado_client, *self.args, **self.kwargs)  # type: ignore[attr-defined]
        return self.resource

    def __exit__(self, *_: Any) -> None:
        if self.delete_after:
            self.resource.delete(self.ado_client)  # type: ignore[attr-defined]


# ============================================================================================== #


def binary_data_to_file_dictionary(binary_data: bytes, file_types: list[str] | None, suppress_warnings: bool) -> dict[str, str]:
    import io
    import zipfile

    bytes_io = io.BytesIO(binary_data)
    files: dict[str, str] = {}

    with zipfile.ZipFile(bytes_io) as zip_ref:
        # For each file, read the bytes and convert to string
        for path in [
            x for x in zip_ref.namelist()
            if file_types is None or (f"{x.split('.')[-1]}" in file_types or f".{x.split('.')[-1]}" in file_types)  # fmt: skip
        ]:
            if path.endswith("/"):  # Ignore directories
                continue
            data = zip_ref.read(path)
            try:
                files[path] = data.decode("utf-8", errors="ignore")
            except UnicodeDecodeError:
                if not suppress_warnings:
                    print(f"[ADO_WRAPPER] Could not decode {path}, leaving it as bytes instead.")
                    files[path] = data  # type: ignore[assignment]

    bytes_io.close()
    return files


# ============================================================================================== #


def get_resource_variables() -> dict[str, type["StateManagedResource"]]:  # We do this whole func to avoid circular imports
    """This returns a mapping of resource name (str) to the class type of the resource. This is used to dynamically create instances of resources."""
    from ado_wrapper.resources import (  # pylint: disable=possibly-unused-variable  # noqa: F401
        AgentPool, AnnotatedTag, Artifact, AuditLog, Branch, BuildTimeline, Build, BuildDefinition, HierarchyCreatedBuildDefinition, Commit, Environment,
        Group, MergePolicies, MergeBranchPolicy, MergePolicyDefaultReviewer, MergeTypeRestrictionPolicy, Organisation, PersonalAccessToken, Permission,
        Project, PullRequest, PullRequestCommentThread, PullRequestComment, Release, ReleaseDefinition, Repo, Run, BuildRepository, Team, AdoUser, Member, SecureFile, ServiceEndpoint,
        Reviewer, VariableGroup,  # fmt: skip
    )

    return locals()


ResourceType = Literal[
    "AgentPool", "AnnotatedTag", "Artifact", "AuditLog", "Branch", "BuildTimeline", "Build", "BuildDefinition", "HierarchyCreatedBuildDefinition",
    "Commit", "Environment", "Group", "MergePolicies", "MergeBranchPolicy", "MergePolicyDefaultReviewer", "MergeTypeRestrictionPolicy",
    "Organisation", "PersonalAccessToken", "Permission", "Project", "PullRequest", "PullRequestCommentThread", "PullRequestComment", "Release", "ReleaseDefinition",
    "Repo", "Run", "Team", "AdoUser", "Member", "SecureFile", "ServiceEndpoint", "Reviewer", "VariableGroup",
]  # fmt: skip
