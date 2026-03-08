from __future__ import annotations

from app.schemas.api_key import (
    ApiKeyCreate,
    ApiKeyCreatedResponse,
    ApiKeyResponse,
    ApiKeysListResponse,
)
from app.schemas.book import (
    BookCopyResponse,
    BookCreate,
    BookDetailResponse,
    BookResponse,
    BookSummary,
    BookUpdate,
    BooksListResponse,
    CopyCreate,
    CopyUpdate,
)
from app.schemas.fine import (
    AdminFineResponse,
    AdminFinesListResponse,
    FineResponse,
    FinesListResponse,
)
from app.schemas.loan import (
    AdminLoanResponse,
    CheckoutRequest,
    LoanHistoryItem,
    LoanHistoryResponse,
    LoanResponse,
    LoansListResponse,
    LostResponse,
    RenewResponse,
    ReturnResponse,
)
from app.schemas.reservation import (
    ReservationResponse,
    ReservationsListResponse,
    ReserveRequest,
)
from app.schemas.review import (
    BookReviewsResponse,
    MyReviewResponse,
    ReviewCreate,
    ReviewResponse,
)
from app.schemas.user import (
    AdminUserDetailResponse,
    AdminUserResponse,
    AdminUsersListResponse,
    PromoteRequest,
    ReadingProfileResponse,
    StatsResponse,
    UserProfileResponse,
    UserUpdate,
)

__all__ = [
    # Book
    "BookSummary",
    "BookResponse",
    "BookCopyResponse",
    "BookDetailResponse",
    "BooksListResponse",
    "BookCreate",
    "BookUpdate",
    "CopyCreate",
    "CopyUpdate",
    # Loan
    "CheckoutRequest",
    "LoanResponse",
    "LoansListResponse",
    "LoanHistoryItem",
    "LoanHistoryResponse",
    "RenewResponse",
    "ReturnResponse",
    "LostResponse",
    "AdminLoanResponse",
    # Reservation
    "ReserveRequest",
    "ReservationResponse",
    "ReservationsListResponse",
    # Fine
    "FineResponse",
    "FinesListResponse",
    "AdminFineResponse",
    "AdminFinesListResponse",
    # Review
    "ReviewCreate",
    "ReviewResponse",
    "MyReviewResponse",
    "BookReviewsResponse",
    # User
    "UserProfileResponse",
    "ReadingProfileResponse",
    "AdminUserResponse",
    "AdminUsersListResponse",
    "AdminUserDetailResponse",
    "UserUpdate",
    "PromoteRequest",
    "StatsResponse",
    # API Key
    "ApiKeyCreate",
    "ApiKeyResponse",
    "ApiKeyCreatedResponse",
    "ApiKeysListResponse",
]
