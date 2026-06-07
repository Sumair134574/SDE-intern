"""
utils/retry.py
Exponential-backoff retry wrapper for HTTP calls.
Retries on transient errors (5xx, connection errors, timeouts).
"""

import time
import functools
from typing import Callable, TypeVar

import requests

T = TypeVar("T")

_RETRYABLE_STATUS = {429, 500, 502, 503, 504}
_MAX_RETRIES = 3
_BASE_DELAY = 1.0  # seconds


def with_retry(fn: Callable[[], T], max_retries: int = _MAX_RETRIES) -> T:
    """
    Call fn() and retry on transient failures with exponential backoff.

    Args:
        fn: A zero-argument callable that returns a requests.Response.
        max_retries: Maximum number of retry attempts.

    Returns:
        The response from fn().

    Raises:
        The last exception if all retries are exhausted.
    """
    last_exc: Exception | None = None

    for attempt in range(max_retries + 1):
        try:
            response = fn()

            # Retry on transient server-side errors
            if response.status_code in _RETRYABLE_STATUS and attempt < max_retries:
                delay = _BASE_DELAY * (2 ** attempt)
                time.sleep(delay)
                continue

            return response

        except (requests.ConnectionError, requests.Timeout) as exc:
            last_exc = exc
            if attempt < max_retries:
                delay = _BASE_DELAY * (2 ** attempt)
                time.sleep(delay)
            else:
                raise

    raise last_exc  # type: ignore[misc]
