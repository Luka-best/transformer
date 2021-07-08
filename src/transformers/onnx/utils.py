# Copyright 2021 The HuggingFace Team. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from pathlib import Path
from typing import Any, Dict, Iterable


def generate_identified_filename(filename: Path, identifier: str) -> Path:
    """
    Append a string-identifier at the end (before the extension, if any) to the provided filepath

    Args:
        filename: pathlib.Path The actual path object we would like to add an identifier suffix
        identifier: The suffix to add

    Returns:
        (str) With concatenated identifier at the end of the filename
    """
    return filename.parent.joinpath(filename.stem + identifier).with_suffix(filename.suffix)


def flatten_output_collection_property(name: str, field: Iterable[Any]) -> Dict[str, Any]:
    """
    Flatten any potential nested structure expanding the name of the field with the index of the element within the
    structure.

    Args:
        name: The name of the nested structure
        field: The structure to, potentially, be flattened

    Returns:
        (Dict[str, Any]): Outputs with flattened structure and key mapping this new structure.

    """
    from itertools import chain

    return {f"{name}.{idx}": item for idx, item in enumerate(chain.from_iterable(field))}
