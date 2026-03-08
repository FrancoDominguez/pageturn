import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text, text
from sqlalchemy.dialects.postgresql import ARRAY, TSVECTOR, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Book(Base):
    __tablename__ = "books"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    author: Mapped[str] = mapped_column(String(500), nullable=False)
    isbn: Mapped[str | None] = mapped_column(String(20), unique=True)
    isbn13: Mapped[str | None] = mapped_column(String(20), unique=True)
    description: Mapped[str | None] = mapped_column(Text)
    genre: Mapped[str | None] = mapped_column(String(100))
    genres = mapped_column(ARRAY(String), server_default="{}")
    item_type: Mapped[str] = mapped_column(String(50), nullable=False, server_default="book")
    cover_image_url: Mapped[str | None] = mapped_column(String(1000))
    page_count: Mapped[int | None] = mapped_column(Integer)
    publication_year: Mapped[int | None] = mapped_column(Integer)
    publisher: Mapped[str | None] = mapped_column(String(500))
    language: Mapped[str | None] = mapped_column(String(10), server_default="en")
    is_staff_pick: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    staff_pick_note: Mapped[str | None] = mapped_column(Text)
    replacement_cost: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    avg_rating: Mapped[Decimal] = mapped_column(Numeric(3, 2), server_default="0.00")
    rating_count: Mapped[int] = mapped_column(Integer, server_default="0")
    search_vector = mapped_column(TSVECTOR)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )

    copies = relationship("BookCopy", back_populates="book", cascade="all, delete-orphan")
    reviews = relationship("Review", back_populates="book")
    reservations = relationship("Reservation", back_populates="book")


class BookCopy(Base):
    __tablename__ = "book_copies"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    book_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("books.id", ondelete="CASCADE"), nullable=False
    )
    barcode: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    condition: Mapped[str] = mapped_column(String(20), nullable=False, server_default="good")
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default="available")
    added_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )

    book = relationship("Book", back_populates="copies")
    loans = relationship("Loan", back_populates="book_copy")
