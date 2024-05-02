import inspect
import re

from ado_wrapper.resources import *

pattern = re.compile(r'(?<!^)(?=[A-Z])')
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
    return pattern.sub('_', string.replace("'", "").strip()).lower().removeprefix("_").replace(" _", " ")

def format_return_type(return_type: str) -> str | None:
    """Returns the value, formatted, and = if it's not None, makes list[`object`] also be called `objects`"""
    return_type = pascal_to_snake(return_type.split(" | ")[0])
    if return_type == "str":
        return f"string_var = "
    if return_type.startswith("dict"):
        return f"dictionary = "
    if return_type.startswith("none"):
        return ""
    if "state_managed_resource" in return_type:
        return None
    if return_type.startswith("list[_"):
        return_type = return_type.removeprefix("list[_").removesuffix("]")+"s"
    return f"{return_type} = "


sorted_pairs = dict(sorted({string: value for string, value in globals().items() if string[0].isupper()}.items()))

for class_name, value in sorted_pairs.items():
    # if class_name != "Project":
    #     continue
    # print([x for x in dir(value) if not x.startswith("_") and x not in ignored_functions])
    function_data = {key: value for key, value in dict(inspect.getmembers(value)).items() if not key.startswith("_") and key not in ignored_functions}
    string += f"-----\n# {class_name}\n<details>\n\n```py\n"
    for function_name, function_args, in function_data.items():
        try:
            signature = inspect.signature(function_args)
        except TypeError:
            pass
        # =======
        comment = function_name.replace("_", " ").title()
        #
        return_type = format_return_type(str(signature.return_annotation))
        if return_type is None:
            continue
        #
        function_args = [x for x in signature.parameters.keys() if x != "self"]
        single_args_formatted = [x if i==0 else f"<{x}>" for i, x in enumerate(function_args)]
        function_args_formatted = ", ".join(single_args_formatted)
        # if "<typing.Any>" in function_args_formatted:
        #     continue
        string += f"# {comment}\n{return_type}{class_name if ' = ' in return_type else pascal_to_snake(class_name)}.{function_name}({function_args_formatted})\n\n"

    string += "\n```\n</details>\n\n"

with open("examples.md", "w") as file:
    file.write(string)

# Build
#   Allow On Environment is broken, below:
#   ado_wrapper.resources.environment._pipeline_authorisation = Build.allow_on_environment(ado_client, <definition_id>, <environment_id>)
# All the updates, which have NotImplementedError, and rely on the parent one which is ugly, maybe rename that tbh to start with _?
# BuildDefinitions (process, revision), Project (last_update_time)