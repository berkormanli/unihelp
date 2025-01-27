from typing import Any

import fastapi

from src.utilities.messages.exceptions.http.exc_details import (
    http_409_post_poll_conflict,
    http_409_poll_already_voted
)

async def http_409_exc_post_already_has_poll_request(*, post_id: int) -> Exception:
    return fastapi.HTTPException(
        status_code=fastapi.status.HTTP_409_CONFLICT,
        detail=http_409_post_poll_conflict(post_id=post_id),
    )

async def http_409_exc_poll_already_voted(*, poll_id: int) -> Exception:
    return fastapi.HTTPException(
        status_code=fastapi.status.HTTP_409_CONFLICT,
        detail=http_409_poll_already_voted(poll_id=poll_id)
    )