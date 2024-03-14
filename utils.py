from datetime import datetime, timezone
from typing import overload


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


class ResourceNotFound(Exception):
    pass


class DeletionFailed(Exception):
    pass


class UnknownError(Exception):
    pass
