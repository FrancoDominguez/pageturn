from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel


class BookSummary(BaseModel):
    id: UUID
    title: str
    author: str
    cover_image_url: str | None = None


class BookResponse(BaseModel):
    id: UUID
    title: str
    author: str
    genre: str | None = None
    item_type: str = "book"
    cover_image_url: str | None = None
    avg_rating: Decimal = Decimal("0.00")
    rating_count: int = 0
    publication_year: int | None = None
    is_staff_pick: bool = False
    staff_pick_note: str | None = None
    available_copies: int = 0
    total_copies: int = 0


class BookCopyResponse(BaseModel):
    id: UUID
    status: str
    condition: str
    barcode: str
    current_borrower: dict | None = None


class BookDetailResponse(BaseModel):
    id: UUID
    title: str
    author: str
    isbn: str | None = None
    isbn13: str | None = None
    description: str | None = None
    genre: str | None = None
    genres: list[str] = []
    item_type: str = "book"
    cover_image_url: str | None = None
    page_count: int | None = None
    publication_year: int | None = None
    publisher: str | None = None
    language: str | None = None
    avg_rating: Decimal = Decimal("0.00")
    rating_count: int = 0
    is_staff_pick: bool = False
    staff_pick_note: str | None = None
    copies: list[BookCopyResponse] = []
    available_copies: int = 0
    total_copies: int = 0
    earliest_return_date: str | None = None
    reservation_count: int = 0
    user_loan: dict | None = None
    user_reservation: dict | None = None


class BooksListResponse(BaseModel):
    books: list[BookResponse]
    total: int
    page: int
    limit: int
    pages: int


class BookCreate(BaseModel):
    title: str
    author: str
    isbn: str | None = None
    isbn13: str | None = None
    description: str | None = None
    genre: str | None = None
    genres: list[str] = []
    item_type: str = "book"
    cover_image_url: str | None = None
    page_count: int | None = None
    publication_year: int | None = None
    publisher: str | None = None
    language: str = "en"
    is_staff_pick: bool = False
    staff_pick_note: str | None = None
    copies: int = 1
    copy_condition: str = "new"


class BookUpdate(BaseModel):
    title: str | None = None
    author: str | None = None
    isbn: str | None = None
    isbn13: str | None = None
    description: str | None = None
    genre: str | None = None
    genres: list[str] | None = None
    item_type: str | None = None
    cover_image_url: str | None = None
    page_count: int | None = None
    publication_year: int | None = None
    publisher: str | None = None
    language: str | None = None
    is_staff_pick: bool | None = None
    staff_pick_note: str | None = None
    replacement_cost: Decimal | None = None


class CopyCreate(BaseModel):
    count: int = 1
    condition: str = "new"


class CopyUpdate(BaseModel):
    status: str | None = None
    condition: str | None = None
