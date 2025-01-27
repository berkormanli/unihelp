"""
The HTTP 404 Not Found response status code indicates that the server cannot find the requested resource.
"""

import fastapi

from src.utilities.messages.exceptions.http.exc_details import (
    http_404_email_details,
    http_404_id_details,
    http_404_username_details,
    http_404_post_id_details,
    http_404_poll_id_details,
    http_404_photo_id_details,
    http_404_comment_id_details,
)


async def http_404_exc_email_not_found_request(email: str) -> Exception:
    return fastapi.HTTPException(
        status_code=fastapi.status.HTTP_404_NOT_FOUND,
        detail=http_404_email_details(email=email),
    )


async def http_404_exc_id_not_found_request(id: int) -> Exception:
    return fastapi.HTTPException(
        status_code=fastapi.status.HTTP_404_NOT_FOUND,
        detail=http_404_id_details(id=id),
    )


async def http_404_exc_username_not_found_request(username: str) -> Exception:
    return fastapi.HTTPException(
        status_code=fastapi.status.HTTP_404_NOT_FOUND,
        detail=http_404_username_details(username=username),
    )

async def http_404_exc_post_id_not_found_request(post_id: int) -> Exception:
    return fastapi.HTTPException(
        status_code=fastapi.status.HTTP_404_NOT_FOUND,
        detail=http_404_post_id_details(post_id=post_id),
    )

async def http_404_exc_poll_id_not_found_request(poll_id: int) -> Exception:
    return fastapi.HTTPException(
        status_code=fastapi.status.HTTP_404_NOT_FOUND,
        detail=http_404_poll_id_details(poll_id=poll_id),
    )

async def http_404_exc_photo_id_not_found_request(photo_id: int) -> Exception:
    return fastapi.HTTPException(
        status_code=fastapi.status.HTTP_404_NOT_FOUND,
        detail=http_404_photo_id_details(photo_id=photo_id),
    )

async def http_404_exc_comment_id_not_found_request(comment_id: int) -> Exception:
    return fastapi.HTTPException(
        status_code=fastapi.status.HTTP_404_NOT_FOUND,
        detail=http_404_comment_id_details(comment_id=comment_id),
    )
