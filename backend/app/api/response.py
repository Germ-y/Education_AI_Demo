from typing import Any
from uuid import uuid4


def ok(data: Any) -> dict[str, Any]:
    return {"data": data, "meta": {"requestId": str(uuid4())}}
