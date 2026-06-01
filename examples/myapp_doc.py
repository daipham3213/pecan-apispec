"""Generate and print the OpenAPI document for :mod:`examples.myapp`.

python -m examples.myapp_doc          # prints JSON
python -m examples.myapp_doc --yaml   # prints YAML (needs the 'yaml' extra)
"""

import json
import sys

# Importing the app module is what populates the registry via the decorators.
import examples.myapp  # noqa: F401  (side-effecting import)
from pecan_apispec import build_dict
from pecan_apispec import build_yaml


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if "--yaml" in argv:
        print(build_yaml("myapp", "1.0"))
    else:
        print(json.dumps(build_dict("myapp", "1.0"), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
