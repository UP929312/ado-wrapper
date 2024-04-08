from datetime import datetime

from ado_wrapper.state_managed_abc import recursively_convert_to_json, recursively_convert_from_json


class TestStateManagedABCs:
    def test_recursively_convert_to_json(self) -> None:
        now = datetime.now()
        raw_input = {
            "id": "123",
            "number": 456,
            "boolean": True,
            "dt_object": now,
            "dict": {"key": "value", "nested": {"key2": "value2"}},
            "list": [1, 2, 3],
        }
        data = dict(recursively_convert_to_json(attribute_name, attribute_value) for attribute_name, attribute_value in raw_input.items())
        assert data == {
            "id": "123",
            "number": "456",
            "boolean": "True",
            "dt_object::datetime": now.isoformat(),
            "dict": {"key": "value", "nested": {"key2": "value2"}},
            "list": ["1", "2", "3"],
        }

    def test_recursively_convert_from_json(self) -> None:
        now = datetime.now()
        raw_input = {
            "id": "123",
            "number": "456",
            "boolean": True,
            "dt_object::datetime": now.isoformat(),
            "dict": {"key": "value", "nested": {"key2": "value2"}},
            "list": ["1", "2", "3"],
        }
        data = recursively_convert_from_json(raw_input)
        assert data == {
            "id": "123",
            "number": "456",
            "boolean": True,
            "dt_object": now,
            "dict": {"key": "value", "nested": {"key2": "value2"}},
            "list": ["1", "2", "3"],
        }
