export interface Book {
  id: string;
  title: string;
  author: string;
  isbn?: string;
  isbn13?: string;
  description?: string;
  genre?: string;
  genres: string[];
  item_type: 'book' | 'audiobook' | 'dvd' | 'ebook' | 'magazine';
  cover_image_url?: string;
  page_count?: number;
  publication_year?: number;
  publisher?: string;
  language: string;
  avg_rating: number;
  rating_count: number;
  available_copies: number;
  total_copies: number;
  is_staff_pick: boolean;
  staff_pick_note?: string;
}

export interface BookDetail extends Book {
  copies: BookCopy[];
  earliest_return_date?: string;
  reservation_count: number;
  user_loan?: Loan;
  user_reservation?: Reservation;
}

export interface BookCopy {
  id: string;
  status: 'available' | 'checked_out' | 'reserved' | 'damaged' | 'lost';
  condition: 'new' | 'good' | 'fair' | 'poor';
  barcode: string;
}

export interface BookSummary {
  id: string;
  title: string;
  author: string;
  cover_image_url?: string;
}

export interface Loan {
  id: string;
  book: BookSummary;
  checked_out_at: string;
  due_date: string;
  returned_at?: string;
  days_remaining: number;
  renewed_count: number;
  can_renew: boolean;
  renewal_blocked_reason?: string;
  status: 'active' | 'returned' | 'overdue';
  accrued_fine?: number;
  daily_rate?: number;
  days_overdue?: number;
}

export interface LoanHistory {
  id: string;
  book: BookSummary;
  checked_out_at: string;
  returned_at?: string;
  was_late: boolean;
  user_review?: { id: string; rating: number };
}

export interface Reservation {
  id: string;
  book: BookSummary;
  status: 'pending' | 'ready' | 'fulfilled' | 'expired' | 'cancelled';
  queue_position?: number;
  expires_at?: string;
  reserved_at: string;
}

export interface Fine {
  id: string;
  book_title: string;
  book_author: string;
  book_cover_url?: string;
  loan_id: string;
  amount: number;
  daily_rate?: number;
  days_overdue?: number;
  reason: 'late_return' | 'lost_item' | 'damaged_item';
  status: 'pending' | 'paid' | 'waived';
  created_at: string;
}

export interface Review {
  id: string;
  user_name: string;
  user_initial: string;
  rating: number;
  review_text?: string;
  created_at: string;
}

export interface MyReview {
  id: string;
  book: BookSummary;
  rating: number;
  review_text?: string;
  created_at: string;
}

export interface UserProfile {
  id: string;
  email: string;
  first_name?: string;
  last_name?: string;
  role: 'user' | 'admin';
  max_loans: number;
  active_loan_count: number;
  outstanding_fines: number;
  created_at: string;
}

export interface ApiKey {
  id: string;
  name: string;
  key_prefix: string;
  scope: 'user' | 'admin';
  last_used_at?: string;
  created_at: string;
  is_active: boolean;
}

// Response types
export interface BooksResponse {
  books: Book[];
  total: number;
  page: number;
  limit: number;
  pages: number;
}

export interface LoansResponse {
  loans: Loan[];
}

export interface LoanHistoryResponse {
  loans: LoanHistory[];
  total: number;
  page: number;
}

export interface ReservationsResponse {
  reservations: Reservation[];
}

export interface FinesResponse {
  fines: Fine[];
  total_outstanding: number;
  checkout_blocked: boolean;
}

export interface ReviewsResponse {
  reviews: Review[];
  avg_rating: number;
  rating_count: number;
  rating_distribution: Record<string, number>;
  total: number;
  page: number;
  limit: number;
}

export interface MyReviewsResponse {
  reviews: MyReview[];
}

export interface ApiKeysResponse {
  api_keys: ApiKey[];
}
