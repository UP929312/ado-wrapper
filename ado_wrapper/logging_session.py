import os
from datetime import datetime
from typing import Any

import requests

DEFAULT_KWARGS = {
    "allow_redirects": True,
    "data": None,
}


class LoggingSession(requests.Session):
    def __init__(self, latest_log_counter: int | None, log_directory: str) -> None:
        super().__init__()
        self.latest_log_counter = latest_log_counter
        self.log_directory = log_directory
        self.log_name = datetime.now().isoformat()

        if not os.path.isdir(self.log_directory):
            os.makedirs(self.log_directory)

        self.cleanup_old_logs()

        with open(f"{self.log_directory}/{self.log_name}.log", "w", encoding="utf-8") as file:
            file.write("")

    def log_request(self, method: str, url: str, args: tuple[Any, ...], kwargs: dict[str, Any]) -> None:
        with open(f"{self.log_directory}/{self.log_name}.log", "a", encoding="utf-8") as file:
            kwargs_copy = dict(kwargs.items())  # Copy
            for default_kwarg, default_kwarg_value in DEFAULT_KWARGS.items():
                # Can't set the default case to None since sometimes that's what we're looking for
                if kwargs.get(default_kwarg, -1) == default_kwarg_value:
                    del kwargs_copy[default_kwarg]
            file.write(f"{method} @ {url}{' | '+str(kwargs_copy) if kwargs_copy else ''}\n")  # {args} |

    def request(self, method: str, url: str, *args: tuple[Any, ...], **kwargs: dict[str, Any]) -> requests.Response:  # type: ignore[override]
        # Log the request using the custom log_request function
        if self.latest_log_counter is not None:
            self.log_request(method, url, args, kwargs)
        # Proceed with the actual request
        return super().request(method, url, *args, **kwargs)  # type: ignore[arg-type]

    def cleanup_old_logs(self) -> None:
        if self.latest_log_counter == -1:
            return
        logs = os.listdir(self.log_directory)
        if self.latest_log_counter is not None and len(logs) < self.latest_log_counter - 1:
            return
        starting_index = self.latest_log_counter - 1 if self.latest_log_counter is not None else 0  # Remove 0 onward
        for file in sorted(logs, reverse=True)[starting_index:]:  # Delete any file that's not the newest x
            os.remove(f"{self.log_directory}/{file}")
