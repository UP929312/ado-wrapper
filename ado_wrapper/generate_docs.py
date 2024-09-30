import inspect
import re

if __name__ == "__main__":
    __import__("sys").path.insert(0, __import__("os").path.abspath(__import__("os").path.dirname(__file__) + "/.."))

from ado_wrapper.resources import *  # pylint: disable=W0401,W0614  # noqa: F401,F403

# TODO: Do replacements, e.g. branchs -> branches

pattern = re.compile(r"(?<!^)(?=[A-Z])")
ignored_functions = ["to_json", "from_json", "from_request_payload", "set_lifecycle_policy"]
string = """<!-- markdownlint-disable MD022 MD031 MD033 -->
<!-- MD022 = Heading should be surrounded by blank lines, MD031 codeblocks should be surrounded by blank lines, MD033 no inline HTML -->
# Examples

All these examples assume an already created AdoClient, perhaps similar to this:

```py
from ado_wrapper import AdoClient

with open("credentials.txt", "r") as file:
    email, ado_access_token, ado_org_name, ado_project = file.read().split("\\n")

ado_client = AdoClient(email, ado_access_token, ado_org_name, ado_project)
```

"""


def pascal_to_snake(string: str) -> str:
    raw_snake_case = pattern.sub("_", string.replace("'", "").strip()).lower()
    return raw_snake_case.removeprefix("_").replace(" _", " ").replace("._", ".").replace("[_", "[")  # Do cleanup


def format_return_type(return_type_input: str) -> str:
    """Returns the value, formatted, and = if it's not None, makes list[`object`] also be called `objects`"""
    if return_type_input.startswith("tuple"):
        components = [
            format_return_type(x).removesuffix(" = ") for x in return_type_input.removeprefix("tuple[").removesuffix("]").split(",")
        ]
        return f"{', '.join(components)} = "
    first_option = return_type_input.split(" | ")[0]  # Get first option (often removes `| None`)
    snake_case = pascal_to_snake(first_option)
    # This converts things like "ado_wrapper.resources.merge_policies.merge_branch_policy" into just merge_branch_policy
    return_type = snake_case.split(".")[-1].removesuffix(">")  # Will remove list[] stuffs as well
    if return_type in ["<class str", "str"]:
        return "string_var = "
    if return_type_input.startswith("dict["):
        # Replace ]] -> ] for 'dict[str, list[ado_wrapper.resources.repo_user_permission.UserPermission]]'
        type_hint = ": " + return_type.replace("any", "Any").replace("]]", "]") if len(return_type_input.split(",")) < 3 else ""
        return f"dictionary{type_hint} = "
    if return_type.startswith("none"):
        return ""
    if return_type_input.startswith("list"):
        return_type = return_type.removeprefix("list[").rstrip("]") + "s"
    return f"{return_type} = "


def dataclass_attributes(cls) -> list[str]:  # type: ignore[no-untyped-def]
    return [x for x in dir(cls) if x in cls.__dataclass_fields__.keys()]


sorted_pairs = dict(sorted({string: value for string, value in globals().items() if string[0].isupper()}.items()))

for class_name, value in sorted_pairs.items():
    function_data = {
        key: value for key, value in dict(inspect.getmembers(value)).items()
        if not key.startswith("_") and key not in ignored_functions and
        key not in dataclass_attributes(globals()[class_name])  # fmt: skip
    }
    if not function_data:
        continue
    string += f"-----\n\n## {class_name}\n<details>\n\n```py\n"
    for function_name, function_args in function_data.items():  # fmt: skip
        try:
            signature = inspect.signature(function_args)
        except TypeError:  # Some random attributes can't be inspected, no worries
            pass
        # =======
        comment = function_name.replace("_", " ").title()
        #
        # if function_name != "get_default_reviewers":
        #     continue
        # print(f"Func={function_name}, Args={function_args}, Return Anno={signature.return_annotation}")
        return_type = format_return_type(str(signature.return_annotation).replace("typing.", ""))
        if return_type is None:
            continue
        #
        function_args = [x for x in signature.parameters.keys() if x != "self"]
        single_args_formatted = [x if x == "ado_client" else f"<{x}>" for x in function_args]  # Wrap non ado_client in <>
        function_args_formatted = ", ".join(single_args_formatted)
        string += f"# {comment}\n{return_type}{class_name if ' = ' in return_type else pascal_to_snake(class_name)}.{function_name}({function_args_formatted})\n\n"

    string += "\n```\n</details>\n\n"

with open("examples.md", "w", encoding="utf-8") as file:
    file.write(string.replace("\n\n\n", "\n").rstrip("\n") + "\n")

# All the functions which have NotImplementedError
