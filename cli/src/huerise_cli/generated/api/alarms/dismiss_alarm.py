from http import HTTPStatus
from typing import Any
from urllib.parse import quote
from uuid import UUID

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.occurrence_read import OccurrenceRead
from ...types import Response


def _get_kwargs(
    alarm_id: UUID,
) -> dict[str, Any]:

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/alarms/{alarm_id}/dismiss".format(
            alarm_id=quote(str(alarm_id), safe=""),
        ),
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | OccurrenceRead | None:
    if response.status_code == 200:
        response_200 = OccurrenceRead.from_dict(response.json())

        return response_200

    if response.status_code == 422:
        response_422 = HTTPValidationError.from_dict(response.json())

        return response_422

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[HTTPValidationError | OccurrenceRead]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    alarm_id: UUID,
    *,
    client: AuthenticatedClient,
) -> Response[HTTPValidationError | OccurrenceRead]:
    """Dismiss Alarm

    Args:
        alarm_id (UUID):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | OccurrenceRead]
    """

    kwargs = _get_kwargs(
        alarm_id=alarm_id,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    alarm_id: UUID,
    *,
    client: AuthenticatedClient,
) -> HTTPValidationError | OccurrenceRead | None:
    """Dismiss Alarm

    Args:
        alarm_id (UUID):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | OccurrenceRead
    """

    return sync_detailed(
        alarm_id=alarm_id,
        client=client,
    ).parsed


async def asyncio_detailed(
    alarm_id: UUID,
    *,
    client: AuthenticatedClient,
) -> Response[HTTPValidationError | OccurrenceRead]:
    """Dismiss Alarm

    Args:
        alarm_id (UUID):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | OccurrenceRead]
    """

    kwargs = _get_kwargs(
        alarm_id=alarm_id,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    alarm_id: UUID,
    *,
    client: AuthenticatedClient,
) -> HTTPValidationError | OccurrenceRead | None:
    """Dismiss Alarm

    Args:
        alarm_id (UUID):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | OccurrenceRead
    """

    return (
        await asyncio_detailed(
            alarm_id=alarm_id,
            client=client,
        )
    ).parsed
