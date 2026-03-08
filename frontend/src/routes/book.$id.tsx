import { useState } from 'react';
import { Link, useParams, useNavigate } from 'react-router-dom';
import { SignedIn, useAuth } from '@clerk/clerk-react';
import { useBookDetail, useBookReviews, useCheckout, useReserveBook, useBookSearch } from '../hooks/useBooks';
import { useCreateReview } from '../hooks/useReviews';
import { useMyFines } from '../hooks/useFines';
import type { Review } from '../types';
import CoverImage from '../components/CoverImage';
import StarRating from '../components/StarRating';
import GenreTag from '../components/GenreTag';
import AvailabilityBadge from '../components/AvailabilityBadge';
import ScrollCard from '../components/ScrollCard';
import LoadingSkeleton from '../components/LoadingSkeleton';
import { useToast } from '../components/Toast';

// ── Rating Distribution Bar ────────────────────────────────────────────────

function RatingBar({ star, count, max }: { star: number; count: number; max: number }) {
  const pct = max > 0 ? (count / max) * 100 : 0;
  return (
    <div className="flex items-center gap-2 text-sm">
      <span className="w-3 text-right text-text-muted">{star}</span>
      <svg className="w-4 h-4 text-amber-400 flex-shrink-0" viewBox="0 0 20 20" fill="currentColor">
        <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
      </svg>
      <div className="flex-1 h-2 bg-gray-100 rounded-full overflow-hidden">
        <div className="h-full bg-amber-400 rounded-full transition-all" style={{ width: `${pct}%` }} />
      </div>
      <span className="w-8 text-right text-text-muted text-xs">{count}</span>
    </div>
  );
}

// ── Review Card ────────────────────────────────────────────────────────────

function ReviewCard({ review }: { review: Review }) {
  return (
    <div className="border-b border-border last:border-0 py-4 first:pt-0">
      <div className="flex items-center gap-3 mb-2">
        <div className="w-8 h-8 rounded-full bg-gradient-to-br from-primary to-secondary flex items-center justify-center text-white text-sm font-semibold flex-shrink-0">
          {review.user_initial}
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-text-primary truncate">{review.user_name}</p>
          <p className="text-xs text-text-muted">{new Date(review.created_at).toLocaleDateString()}</p>
        </div>
        <StarRating rating={review.rating} size="sm" />
      </div>
      {review.review_text && (
        <p className="text-sm text-text-secondary leading-relaxed">{review.review_text}</p>
      )}
    </div>
  );
}

// ── Review Form ────────────────────────────────────────────────────────────

function ReviewForm({ bookId }: { bookId: string }) {
  const [rating, setRating] = useState(0);
  const [text, setText] = useState('');
  const createReview = useCreateReview();
  const { toast } = useToast();

  const handleSubmit = () => {
    if (rating === 0) return;
    createReview.mutate(
      { book_id: bookId, rating, review_text: text || undefined },
      {
        onSuccess: () => {
          toast('Review submitted!', 'success');
          setRating(0);
          setText('');
        },
        onError: () => toast('Failed to submit review.', 'error'),
      },
    );
  };

  return (
    <div className="bg-surface rounded-card p-5 shadow-card">
      <h3 className="font-heading font-semibold text-base text-text-primary mb-3">Write a Review</h3>
      <div className="mb-3">
        <StarRating rating={rating} interactive onChange={setRating} size="lg" />
      </div>
      <textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder="Share your thoughts about this book..."
        className="w-full h-24 p-3 text-sm text-text-primary bg-background border border-border rounded-card resize-none focus:ring-2 focus:ring-primary/40 focus:outline-none placeholder:text-text-muted"
      />
      <div className="mt-3 flex justify-end">
        <button
          type="button"
          onClick={handleSubmit}
          disabled={rating === 0 || createReview.isPending}
          className="px-5 py-2 bg-primary hover:bg-primary-hover text-white text-sm font-medium rounded-button transition-colors disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
        >
          {createReview.isPending ? 'Submitting...' : 'Submit Review'}
        </button>
      </div>
    </div>
  );
}

// ── Metadata Grid Item ─────────────────────────────────────────────────────

function MetaItem({ label, value }: { label: string; value?: string | number | null }) {
  if (value == null || value === '') return null;
  return (
    <div>
      <dt className="text-xs text-text-muted uppercase tracking-wider">{label}</dt>
      <dd className="text-sm text-text-primary font-medium mt-0.5">{value}</dd>
    </div>
  );
}

// ── Main Page ──────────────────────────────────────────────────────────────

export default function BookDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { isSignedIn } = useAuth();
  const { toast } = useToast();

  const { data: book, isLoading: bookLoading } = useBookDetail(id!);
  const { data: reviewsData } = useBookReviews(id!);
  const { data: finesData } = useMyFines();
  const checkout = useCheckout();
  const reserve = useReserveBook();

  // More by author
  const { data: moreByAuthor } = useBookSearch(
    book ? { author: book.author, limit: '10' } : { limit: '0' },
  );
  const authorBooks = moreByAuthor?.books?.filter((b) => b.id !== id) ?? [];

  // Action state
  const [actionBanner, setActionBanner] = useState<{
    type: 'success' | 'info' | 'error';
    message: string;
  } | null>(null);

  const finesBlocked = (finesData?.total_outstanding ?? 0) >= 10;

  const handleCheckout = () => {
    if (!isSignedIn) {
      navigate('/sign-in');
      return;
    }
    if (finesBlocked) {
      setActionBanner({
        type: 'error',
        message: 'You have outstanding fines of $10 or more. Please pay your fines before checking out.',
      });
      return;
    }
    checkout.mutate(id!, {
      onSuccess: () => {
        setActionBanner({ type: 'success', message: 'Book checked out successfully! Due in 14 days.' });
        toast('Book checked out!', 'success');
      },
      onError: (err) => {
        setActionBanner({ type: 'error', message: err.message || 'Checkout failed.' });
      },
    });
  };

  const handleReserve = () => {
    if (!isSignedIn) {
      navigate('/sign-in');
      return;
    }
    reserve.mutate(id!, {
      onSuccess: () => {
        setActionBanner({ type: 'info', message: 'Reservation placed! We\'ll notify you when a copy is available.' });
        toast('Reservation placed!', 'success');
      },
      onError: (err) => {
        setActionBanner({ type: 'error', message: err.message || 'Reservation failed.' });
      },
    });
  };

  if (bookLoading) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 py-8">
        <LoadingSkeleton type="detail" />
      </div>
    );
  }

  if (!book) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 py-16">
        <EmptyState title="Book not found" description="This book may have been removed." action={{ label: 'Browse Library', href: '/' }} />
      </div>
    );
  }

  const canCheckOut = book.available_copies > 0 && !book.user_loan;
  const canReserve = book.available_copies === 0 && !book.user_reservation;
  const hasReturnedLoan = book.user_loan?.status === 'returned';

  const bannerColors = {
    success: 'bg-emerald-50 border-emerald-200 text-emerald-800',
    info: 'bg-blue-50 border-blue-200 text-blue-800',
    error: 'bg-red-50 border-red-200 text-red-800',
  };

  // Rating distribution
  const distribution = reviewsData?.rating_distribution ?? {};
  const maxDistCount = Math.max(...Object.values(distribution).map(Number), 1);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 py-8">
      {/* Breadcrumb */}
      <nav className="flex items-center gap-2 text-sm text-text-muted mb-6">
        <Link to="/" className="hover:text-primary transition-colors">Home</Link>
        <span>/</span>
        <span className="text-text-primary truncate">{book.title}</span>
      </nav>

      {/* Action banner */}
      {actionBanner && (
        <div className={`mb-6 p-4 rounded-card border text-sm font-medium ${bannerColors[actionBanner.type]}`}>
          {actionBanner.message}
        </div>
      )}

      {/* Two-column layout */}
      <div className="flex flex-col md:flex-row gap-8 md:gap-12">
        {/* Left: Cover */}
        <div className="w-full md:w-[40%] flex-shrink-0">
          <div className="sticky top-24">
            <div className="relative">
              <CoverImage
                src={book.cover_image_url}
                title={book.title}
                author={book.author}
                className="w-full aspect-[2/3] rounded-card shadow-hover"
              />
              {book.is_staff_pick && (
                <div className="absolute top-3 left-3 inline-flex items-center gap-1.5 px-3 py-1.5 bg-[#0d1117]/90 backdrop-blur-sm text-white text-xs font-medium rounded-pill">
                  <svg className="w-3.5 h-3.5 text-amber-400" fill="currentColor" viewBox="0 0 20 20">
                    <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                  </svg>
                  Staff Pick
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Right: Metadata */}
        <div className="flex-1 min-w-0">
          <h1 className="font-heading text-[36px] font-bold text-text-primary leading-tight mb-2">
            {book.title}
          </h1>

          <Link
            to={`/?author=${encodeURIComponent(book.author)}`}
            className="text-primary hover:text-primary-hover text-lg font-medium transition-colors"
          >
            {book.author}
          </Link>

          <div className="mt-3">
            <StarRating rating={book.avg_rating} count={book.rating_count} size="md" />
          </div>

          {/* Genre pills */}
          {book.genres.length > 0 && (
            <div className="flex flex-wrap gap-2 mt-4">
              {book.genres.map((g) => (
                <GenreTag key={g} genre={g} onClick={() => navigate(`/?genre=${encodeURIComponent(g)}`)} />
              ))}
            </div>
          )}

          {/* Metadata grid */}
          <dl className="grid grid-cols-2 sm:grid-cols-3 gap-x-6 gap-y-3 mt-6 pb-6 border-b border-border">
            <MetaItem label="Pages" value={book.page_count} />
            <MetaItem label="Published" value={book.publication_year} />
            <MetaItem label="Format" value={book.item_type.charAt(0).toUpperCase() + book.item_type.slice(1)} />
            <MetaItem label="Language" value={book.language} />
            <MetaItem label="ISBN" value={book.isbn13 || book.isbn} />
            <MetaItem label="Publisher" value={book.publisher} />
          </dl>

          {/* Description */}
          {book.description && (
            <div className="mt-6">
              <p className="text-sm text-text-secondary leading-relaxed">{book.description}</p>
            </div>
          )}

          {/* Availability */}
          <div className="mt-6">
            <AvailabilityBadge
              availableCopies={book.available_copies}
              totalCopies={book.total_copies}
              userHasBook={!!book.user_loan && book.user_loan.status !== 'returned'}
              isOverdue={book.user_loan?.status === 'overdue'}
            />
            {book.earliest_return_date && book.available_copies === 0 && (
              <p className="text-xs text-text-muted mt-1.5">
                Earliest expected return: {new Date(book.earliest_return_date).toLocaleDateString()}
              </p>
            )}
          </div>

          {/* Action buttons */}
          <div className="flex flex-wrap gap-3 mt-6">
            {canCheckOut && (
              <button
                type="button"
                onClick={handleCheckout}
                disabled={checkout.isPending}
                className="inline-flex items-center px-6 py-3 bg-gradient-to-r from-primary to-secondary text-white text-sm font-semibold rounded-pill hover:opacity-90 transition-opacity disabled:opacity-50 cursor-pointer disabled:cursor-not-allowed shadow-card"
              >
                {checkout.isPending ? 'Checking out...' : 'Check Out'}
              </button>
            )}
            {canReserve && (
              <button
                type="button"
                onClick={handleReserve}
                disabled={reserve.isPending}
                className="inline-flex items-center px-6 py-3 border-2 border-primary text-primary text-sm font-semibold rounded-pill hover:bg-primary/5 transition-colors disabled:opacity-50 cursor-pointer disabled:cursor-not-allowed"
              >
                {reserve.isPending ? 'Reserving...' : 'Reserve'}
              </button>
            )}
            {book.user_loan && book.user_loan.status !== 'returned' && (
              <Link
                to="/loans"
                className="inline-flex items-center px-6 py-3 border border-border text-text-secondary text-sm font-medium rounded-pill hover:bg-gray-50 transition-colors"
              >
                View My Loans
              </Link>
            )}
            {book.user_reservation && (
              <span className="inline-flex items-center px-4 py-2 text-sm text-text-muted">
                Reserved (position #{book.user_reservation.queue_position ?? '?'})
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Reviews section */}
      <section className="mt-12 pt-8 border-t border-border">
        <h2 className="font-heading font-bold text-2xl text-text-primary mb-6">Reviews</h2>

        <div className="flex flex-col lg:flex-row gap-8">
          {/* Rating summary */}
          <div className="w-full lg:w-64 flex-shrink-0">
            <div className="bg-surface rounded-card p-5 shadow-card">
              <div className="text-center mb-4">
                <span className="font-heading text-5xl font-bold text-text-primary">
                  {book.avg_rating.toFixed(1)}
                </span>
                <div className="mt-1">
                  <StarRating rating={book.avg_rating} size="md" />
                </div>
                <p className="text-sm text-text-muted mt-1">
                  {book.rating_count.toLocaleString()} {book.rating_count === 1 ? 'review' : 'reviews'}
                </p>
              </div>
              <div className="space-y-1.5">
                {[5, 4, 3, 2, 1].map((star) => (
                  <RatingBar
                    key={star}
                    star={star}
                    count={Number(distribution[String(star)] ?? 0)}
                    max={maxDistCount}
                  />
                ))}
              </div>
            </div>
          </div>

          {/* Review list + form */}
          <div className="flex-1 min-w-0">
            <SignedIn>
              {hasReturnedLoan && !reviewsData?.reviews.some(() => false) && (
                <div className="mb-6">
                  <ReviewForm bookId={id!} />
                </div>
              )}
            </SignedIn>

            {reviewsData?.reviews && reviewsData.reviews.length > 0 ? (
              <div>
                {reviewsData.reviews.map((review) => (
                  <ReviewCard key={review.id} review={review} />
                ))}
              </div>
            ) : (
              <p className="text-text-muted text-sm py-8 text-center">
                No reviews yet. Be the first to review this book!
              </p>
            )}
          </div>
        </div>
      </section>

      {/* More by Author */}
      {authorBooks.length > 0 && (
        <section className="mt-12 pt-8 border-t border-border">
          <h2 className="font-heading font-bold text-xl text-text-primary mb-4">
            More by {book.author}
          </h2>
          <div className="flex gap-3 overflow-x-auto pb-2 scrollbar-hide">
            {authorBooks.map((b) => (
              <div key={b.id} className="snap-start">
                <ScrollCard book={b} />
              </div>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}

// Inline fallback EmptyState (avoids extra import for one usage)
function EmptyState({ title, description, action }: { title: string; description: string; action: { label: string; href: string } }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 px-4 text-center">
      <h3 className="font-heading font-semibold text-lg text-text-primary mb-1">{title}</h3>
      <p className="text-text-muted text-sm max-w-sm mb-6">{description}</p>
      <Link
        to={action.href}
        className="inline-flex items-center px-5 py-2.5 bg-primary hover:bg-primary-hover text-white text-sm font-medium rounded-button transition-colors"
      >
        {action.label}
      </Link>
    </div>
  );
}
