"""Pagination utilities for API responses."""

from __future__ import annotations


def build_paginated_response[T](
    items: list[T], total: int, page: int, page_size: int
) -> dict[str, list[T] | int | bool]:
    """Build a paginated response from query results.

    Args:
        items: List of items for the current page
        total: Total number of items across all pages
        page: Current page number (1-indexed)
        page_size: Number of items per page

    Returns:
        Dictionary with pagination metadata and data
    """
    total_pages = (total + page_size - 1) // page_size if total > 0 else 0
    has_more = page < total_pages

    return {
        "data": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "has_more": has_more,
    }
