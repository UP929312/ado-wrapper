import inspect
import re

from ado_wrapper.resources import *  # pylint: disable=W0401,W0614

pattern = re.compile(r"(?<!^)(?=[A-Z])")
ignored_functions = ["get_by_url", "to_json", "from_json", "get_by_abstract_filter", "from_request_payload", "set_lifecycle_policy"]
string = """

# Examples

All these examples assume an already created AdoClient, perhaps similar to this:

```py
from ado_wrapper import AdoClient

with open("credentials.txt", "r") as file:
    email, ado_access_token, ado_org, ado_project = file.read().split("\\n")

ado_client = AdoClient(email, ado_access_token, ado_org, ado_project)
```

"""


def pascal_to_snake(string: str) -> str:
    return pattern.sub("_", string.replace("'", "").strip()).lower().removeprefix("_").replace(" _", " ")


def format_return_type(return_type: str) -> str | None:
    """Returns the value, formatted, and = if it's not None, makes list[`object`] also be called `objects`"""
    return_type = pascal_to_snake(return_type.split(" | ")[0])
    if "." in return_type:
        return_type = return_type.split(".")[-1].removesuffix(">").removeprefix("_")
    if return_type == "str":
        return "string_var = "
    if return_type.startswith("dict"):
        return "dictionary = "
    if return_type.startswith("none"):
        return ""
    if "state_managed_resource" in return_type:
        return None
    if return_type.startswith("list[_"):
        return_type = return_type.removeprefix("list[_").removesuffix("]") + "s"
    return f"{return_type} = "


def dataclass_attributes(cls) -> list[str]:  # type: ignore[no-untyped-def]
    return [x for x in dir(cls) if x in cls.__dataclass_fields__.keys()]


sorted_pairs = dict(sorted({string: value for string, value in globals().items() if string[0].isupper()}.items()))

for class_name, value in sorted_pairs.items():
    # if class_name != "Build":
    #     continue
    function_data = {
        key: value for key, value in dict(inspect.getmembers(value)).items()
        if not key.startswith("_") and key not in ignored_functions and
        key not in dataclass_attributes(globals()[class_name])  # fmt: skip
    }
    if not function_data:
        continue
    string += f"-----\n# {class_name}\n<details>\n\n```py\n"
    for function_name, function_args in function_data.items():  # fmt: skip
        try:
            signature = inspect.signature(function_args)
        except TypeError:  # Some random attributes can't be inspected, no worries
            pass
        # =======
        comment = function_name.replace("_", " ").title()
        #
        return_type = format_return_type(str(signature.return_annotation))
        if return_type is None:
            continue
        #
        function_args = [x for x in signature.parameters.keys() if x != "self"]
        if function_args == ["ado_client", "update_action", "url", "attribute_name", "attribute_value", "params"]:
            continue  # For things inheritting from update, for the time being before we remap to _update
        single_args_formatted = [x if i == 0 else f"<{x}>" for i, x in enumerate(function_args)]
        function_args_formatted = ", ".join(single_args_formatted)
        string += f"# {comment}\n{return_type}{class_name if ' = ' in return_type else pascal_to_snake(class_name)}.{function_name}({function_args_formatted})\n\n"

    string += "\n```\n</details>\n\n"

with open("examples.md", "w", encoding="utf-8") as file:
    file.write(string.replace("\n\n\n", "\n"))

# All the functions which have NotImplementedError
