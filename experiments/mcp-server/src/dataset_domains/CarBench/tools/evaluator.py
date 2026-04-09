import json
from hashlib import sha256
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from mcp_server import mcp

from dataset_domains.CarBench.context.dynamic_context_state import context_state


Hashable = Union[str, int, float, Tuple["Hashable"], Tuple[Tuple[str, "Hashable"]]]
ToHashable = Union[
    str, int, float, Dict[str, "ToHashable"], List["ToHashable"], Set["ToHashable"]
]


def consistent_hash(
    value: Hashable,
) -> str:
    return sha256(str(value).encode("utf-8")).hexdigest()


def to_hashable(item: ToHashable) -> Hashable:
    if isinstance(item, dict):
        return tuple((key, to_hashable(value)) for key, value in sorted(item.items()))
    elif isinstance(item, list):
        return tuple(to_hashable(element) for element in item)
    elif isinstance(item, set):
        return tuple(sorted(to_hashable(element) for element in item))
    else:
        return item


all_state_hashes = []


@mcp.tool(
    meta={
        "disclose_to_model": False,
    }
)
def get_current_state_hash() -> str:
    return consistent_hash(to_hashable(context_state.get()))


@mcp.tool(
    meta={
        "disclose_to_model": False,
    }
)
def get_all_state_hashes() -> List[str]:
    return all_state_hashes


def append_current_state_hash() -> None:
    current_hash = consistent_hash(to_hashable(context_state.get()))
    all_state_hashes.append(current_hash)
