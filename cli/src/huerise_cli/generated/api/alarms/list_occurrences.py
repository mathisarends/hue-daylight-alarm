from http import HTTPStatus
from typing import Any
from urllib.parse import quote
from uuid import UUID

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.occurrence_read import OccurrenceRead
from ...types import UNSET, Response, Unset


def _get_kwargs(
    alarm_id: UUID,
    *,
    limit: int | Unset = 20,
) -> dict[str, Any]:

    params: dict[str, Any] = {}

    params["limit"] = limit

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/alarms/{alarm_id}/occurrences".format(
            alarm_id=quote(str(alarm_id), safe=""),
        ),
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | list[OccurrenceRead] | None:
    if response.status_code == 200:
        response_200 = []
        _response_200 = response.json()
        for response_200_item_data in _response_200:
            response_200_item = OccurrenceRead.from_dict(response_200_item_data)

            response_200.append(response_200_item)

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
) -> Response[HTTPValidationError | list[OccurrenceRead]]:
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
    limit: int | Unset = 20,
) -> Response[HTTPValidationError | list[OccurrenceRead]]:
    """List Occurrences

    Args:
        alarm_id (UUID):
        limit (int | Unset):  Default: 20.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | list[OccurrenceRead]]
    """

    kwargs = _get_kwargs(
        alarm_id=alarm_id,
        limit=limit,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    alarm_id: UUID,
    *,
    client: AuthenticatedClient,
    limit: int | Unset = 20,
) -> HTTPValidationError | list[OccurrenceRead] | None:
    """List Occurrences

    Args:
        alarm_id (UUID):
        limit (int | Unset):  Default: 20.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | list[OccurrenceRead]
    """

    return sync_detailed(
        alarm_id=alarm_id,
        client=client,
        limit=limit,
    ).parsed


async def asyncio_detailed(
    alarm_id: UUID,
    *,
    client: AuthenticatedClient,
    limit: int | Unset = 20,
) -> Response[HTTPValidationError | list[OccurrenceRead]]:
    """List Occurrences

    Args:
        alarm_id (UUID):
        limit (int | Unset):  Default: 20.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | list[OccurrenceRead]]
    """

    kwargs = _get_kwargs(
        alarm_id=alarm_id,
        limit=limit,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    alarm_id: UUID,
    *,
    client: AuthenticatedClient,
    limit: int | Unset = 20,
) -> HTTPValidationError | list[OccurrenceRead] | None:
    """List Occurrences

    Args:
        alarm_id (UUID):
        limit (int | Unset):  Default: 20.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | list[OccurrenceRead]
    """

    return (
        await asyncio_detailed(
            alarm_id=alarm_id,
            client=client,
            limit=limit,
        )
    ).parsed
