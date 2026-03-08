import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useMyReviews, useUpdateReview, useDeleteReview } from '../hooks/useReviews';
import type { MyReview } from '../types';
import CoverImage from '../components/CoverImage';
import StarRating from '../components/StarRating';
import LoadingSkeleton from '../components/LoadingSkeleton';
import EmptyState from '../components/EmptyState';
import Modal from '../components/Modal';
import { useToast } from '../components/Toast';

// ── Review Card ────────────────────────────────────────────────────────────

function ReviewCard({
  review,
  onEdit,
  onDelete,
}: {
  review: MyReview;
  onEdit: (review: MyReview) => void;
  onDelete: (review: MyReview) => void;
}) {
  const [expanded, setExpanded] = useState(false);
  const isLong = (review.review_text?.length ?? 0) > 200;

  return (
    <div className="bg-surface rounded-card shadow-card p-5">
      <div className="flex gap-4">
        {/* Cover thumbnail */}
        <Link to={`/books/${review.book.id}`} className="flex-shrink-0">
          <CoverImage
            src={review.book.cover_image_url}
            title={review.book.title}
            author={review.book.author}
            className="w-16 h-24 rounded object-cover"
          />
        </Link>

        {/* Content */}
        <div className="flex-1 min-w-0">
          <Link
            to={`/books/${review.book.id}`}
            className="font-heading font-semibold text-sm text-text-primary hover:text-primary transition-colors line-clamp-1"
          >
            {review.book.title}
          </Link>
          <p className="text-xs text-text-muted mt-0.5">{review.book.author}</p>

          <div className="mt-2">
            <StarRating rating={review.rating} size="sm" />
          </div>

          {review.review_text && (
            <div className="mt-2">
              <p className={`text-sm text-text-secondary leading-relaxed ${!expanded && isLong ? 'line-clamp-3' : ''}`}>
                {review.review_text}
              </p>
              {isLong && (
                <button
                  type="button"
                  onClick={() => setExpanded(!expanded)}
                  className="text-xs text-primary font-medium mt-1 cursor-pointer hover:text-primary-hover transition-colors"
                >
                  {expanded ? 'Show less' : 'Read more'}
                </button>
              )}
            </div>
          )}

          <div className="flex items-center justify-between mt-3 pt-3 border-t border-border">
            <span className="text-xs text-text-muted">
              {new Date(review.created_at).toLocaleDateString()}
            </span>
            <div className="flex items-center gap-3">
              <button
                type="button"
                onClick={() => onEdit(review)}
                className="text-xs font-medium text-text-secondary hover:text-primary transition-colors cursor-pointer"
              >
                Edit
              </button>
              <button
                type="button"
                onClick={() => onDelete(review)}
                className="text-xs font-medium text-red-500 hover:text-red-600 transition-colors cursor-pointer"
              >
                Delete
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// ── Edit Form ──────────────────────────────────────────────────────────────

function EditReviewForm({
  review,
  onClose,
}: {
  review: MyReview;
  onClose: () => void;
}) {
  const [rating, setRating] = useState(review.rating);
  const [text, setText] = useState(review.review_text ?? '');
  const updateReview = useUpdateReview();
  const { toast } = useToast();

  const handleSave = () => {
    if (rating === 0) return;
    updateReview.mutate(
      { reviewId: review.id, rating, review_text: text || undefined },
      {
        onSuccess: () => {
          toast('Review updated!', 'success');
          onClose();
        },
        onError: () => toast('Failed to update review.', 'error'),
      },
    );
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3">
        <CoverImage
          src={review.book.cover_image_url}
          title={review.book.title}
          author={review.book.author}
          className="w-12 h-18 rounded flex-shrink-0 object-cover"
        />
        <div>
          <p className="font-heading font-semibold text-sm text-text-primary">{review.book.title}</p>
          <p className="text-xs text-text-muted">{review.book.author}</p>
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-text-primary mb-1.5">Rating</label>
        <StarRating rating={rating} interactive onChange={setRating} size="lg" />
      </div>

      <div>
        <label className="block text-sm font-medium text-text-primary mb-1.5">Review</label>
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          className="w-full h-28 p-3 text-sm text-text-primary bg-background border border-border rounded-card resize-none focus:ring-2 focus:ring-primary/40 focus:outline-none placeholder:text-text-muted"
          placeholder="Share your thoughts..."
        />
      </div>

      <div className="flex justify-end gap-3">
        <button
          type="button"
          onClick={onClose}
          className="px-4 py-2 text-sm font-medium text-text-secondary border border-border rounded-button hover:bg-gray-50 transition-colors cursor-pointer"
        >
          Cancel
        </button>
        <button
          type="button"
          onClick={handleSave}
          disabled={rating === 0 || updateReview.isPending}
          className="px-4 py-2 bg-primary hover:bg-primary-hover text-white text-sm font-medium rounded-button transition-colors disabled:opacity-50 cursor-pointer disabled:cursor-not-allowed"
        >
          {updateReview.isPending ? 'Saving...' : 'Save Changes'}
        </button>
      </div>
    </div>
  );
}

// ── Main Page ──────────────────────────────────────────────────────────────

export default function MyReviewsPage() {
  const { data, isLoading } = useMyReviews();
  const deleteReview = useDeleteReview();
  const { toast } = useToast();

  const [editingReview, setEditingReview] = useState<MyReview | null>(null);
  const [deletingReview, setDeletingReview] = useState<MyReview | null>(null);

  const reviews = data?.reviews ?? [];

  const handleConfirmDelete = () => {
    if (!deletingReview) return;
    deleteReview.mutate(deletingReview.id, {
      onSuccess: () => {
        toast('Review deleted.', 'success');
        setDeletingReview(null);
      },
      onError: () => toast('Failed to delete review.', 'error'),
    });
  };

  if (isLoading) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 py-8">
        <h1 className="font-heading font-bold text-2xl text-text-primary mb-6">My Reviews</h1>
        <LoadingSkeleton type="list" />
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 py-8">
      <h1 className="font-heading font-bold text-2xl text-text-primary mb-6">
        My Reviews
        {reviews.length > 0 && (
          <span className="text-text-muted text-lg font-normal ml-2">({reviews.length})</span>
        )}
      </h1>

      {reviews.length === 0 ? (
        <EmptyState
          title="No reviews yet"
          description="After returning a book, come back here to share your thoughts."
          action={{ label: 'Browse Library', href: '/' }}
          icon={
            <svg className="w-12 h-12" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
            </svg>
          }
        />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {reviews.map((review) => (
            <ReviewCard
              key={review.id}
              review={review}
              onEdit={setEditingReview}
              onDelete={setDeletingReview}
            />
          ))}
        </div>
      )}

      {/* Edit modal */}
      <Modal
        isOpen={!!editingReview}
        onClose={() => setEditingReview(null)}
        title="Edit Review"
      >
        {editingReview && (
          <EditReviewForm review={editingReview} onClose={() => setEditingReview(null)} />
        )}
      </Modal>

      {/* Delete confirmation modal */}
      <Modal
        isOpen={!!deletingReview}
        onClose={() => setDeletingReview(null)}
        title="Delete Review"
      >
        <div className="space-y-4">
          <p className="text-sm text-text-secondary">
            Are you sure you want to delete your review for{' '}
            <strong>"{deletingReview?.book.title}"</strong>? This action cannot be undone.
          </p>
          <div className="flex justify-end gap-3">
            <button
              type="button"
              onClick={() => setDeletingReview(null)}
              className="px-4 py-2 text-sm font-medium text-text-secondary border border-border rounded-button hover:bg-gray-50 transition-colors cursor-pointer"
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={handleConfirmDelete}
              disabled={deleteReview.isPending}
              className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white text-sm font-medium rounded-button transition-colors disabled:opacity-50 cursor-pointer disabled:cursor-not-allowed"
            >
              {deleteReview.isPending ? 'Deleting...' : 'Delete Review'}
            </button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
