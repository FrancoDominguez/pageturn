import { Link } from 'react-router-dom';
import type { Book } from '../types';
import CoverImage from './CoverImage';
import StarRating from './StarRating';
import GenreTag from './GenreTag';
import AvailabilityBadge from './AvailabilityBadge';
import ItemTypeBadge from './ItemTypeBadge';

interface BookCardProps {
  book: Book;
  onClick?: () => void;
}

export default function BookCard({ book, onClick }: BookCardProps) {
  return (
    <Link
      to={`/books/${book.id}`}
      onClick={onClick}
      className="group block bg-surface rounded-card shadow-card hover:shadow-hover hover:-translate-y-0.5 transition-all duration-200 overflow-hidden"
    >
      {/* Cover */}
      <CoverImage
        src={book.cover_image_url}
        title={book.title}
        author={book.author}
        className="w-full aspect-[2/3] rounded-t-card"
      />

      {/* Info */}
      <div className="p-3 space-y-1.5">
        <h3 className="font-heading font-semibold text-sm text-text-primary leading-snug line-clamp-2 group-hover:text-primary transition-colors">
          {book.title}
        </h3>
        <p className="text-xs text-text-muted truncate">
          {book.author}
        </p>

        <StarRating rating={book.avg_rating} count={book.rating_count} size="sm" />

        <div className="flex flex-wrap items-center gap-1.5 pt-0.5">
          {book.item_type !== 'book' && (
            <ItemTypeBadge itemType={book.item_type} />
          )}
          {book.genres[0] && (
            <GenreTag genre={book.genres[0]} />
          )}
        </div>

        <div className="pt-1">
          <AvailabilityBadge
            availableCopies={book.available_copies}
            totalCopies={book.total_copies}
          />
        </div>
      </div>
    </Link>
  );
}
