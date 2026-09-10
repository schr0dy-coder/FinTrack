"""Pagination helper functions."""

import math


def calculate_pages(total: int, limit: int) -> int:
    """Calculate total pages from item count and page limit."""
    if limit <= 0:
        return 1
    return max(1, math.ceil(total / limit))
