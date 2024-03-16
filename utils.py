from datetime import datetime, timezone
from typing import overload, TYPE_CHECKING, Literal, Any
from dataclasses import fields

if TYPE_CHECKING:
    from state_managed_abc import StateManagedResource


@overload
def from_ado_date_string(date_string: str) -> datetime:
    ...


@overload
def from_ado_date_string(date_string: None) -> None:
    ...


def from_ado_date_string(date_string: str | None) -> datetime | None:
    if date_string is None:
        return None
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
    for field_name, metadata in get_fields_metadata(cls).items():
        if metadata.get("is_id_field", False):
            return field_name
    raise ValueError(f"No id field found for {cls.__name__}!")


def extract_id(obj: "StateManagedResource") -> Any:
    id_field_name = get_id_field_name(obj.__class__)
    return getattr(obj, id_field_name)


def get_editable_fields(cls: type["StateManagedResource"]) -> list[str]:
    return [field_obj.name for field_obj in cls.__dataclass_fields__.values() if field_obj.metadata.get("editable", False)]


def get_internal_field_names(cls: type["StateManagedResource"], field_names: list[str] | None = None, reverse: bool = True) -> dict[str, str]:  # fmt: skip
    """Returns a mapping of field names to their internal names. If no internal name is set, the field name is used."""
    if field_names is None:
        field_names = get_editable_fields(cls)
    value = {field_name: cls.__dataclass_fields__[field_name].metadata.get("internal_name", field_name) for field_name in field_names}
    if reverse:
        return {v: k for k, v in value.items()}
    return value


class ResourceNotFound(Exception):
    pass


class DeletionFailed(Exception):
    pass


class ResourceAlreadyExists(Exception):
    pass


class UnknownError(Exception):
    pass


class InvalidPermissionsError(Exception):
    pass


def get_resource_variables() -> dict[str, type["StateManagedResource"]]:  # We do this to avoid circular imports
    from resources import (  # type: ignore[attr-defined]  # pylint: disable=possibly-unused-variable
        Branch, Build, BuildDefinition, Commit, Project, PullRequest, Release, ReleaseDefinition, Repo, Team,
        AdoUser, Member, Reviewer, VariableGroup,  # fmt: skip
    )

    return dict(locals().items())


ResourceType = Literal[
    "Branch", "Build", "BuildDefinition", "Commit", "Project", "PullRequest", "Release", "ReleaseDefinition", "Repo",
    "Team", "AdoUser", "Member", "Reviewer", "VariableGroup"  # fmt: skip
]
