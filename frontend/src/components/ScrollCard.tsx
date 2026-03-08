import { Link } from 'react-router-dom';
import type { Book } from '../types';
import CoverImage from './CoverImage';
import StarRating from './StarRating';

interface ScrollCardProps {
  book: Book;
}

export default function ScrollCard({ book }: ScrollCardProps) {
  const isAvailable = book.available_copies > 0;

  return (
    <Link
      to={`/books/${book.id}`}
      className="group w-40 flex-shrink-0 bg-surface rounded-card shadow-card hover:shadow-hover hover:-translate-y-0.5 transition-all duration-200 overflow-hidden"
    >
      {/* Cover */}
      <CoverImage
        src={book.cover_image_url}
        title={book.title}
        author={book.author}
        className="w-full h-56 rounded-t-card"
      />

      {/* Info */}
      <div className="p-2.5 space-y-1">
        <h3 className="font-heading font-semibold text-xs text-text-primary leading-snug truncate group-hover:text-primary transition-colors">
          {book.title}
        </h3>
        <p className="text-[11px] text-text-muted truncate">
          {book.author}
        </p>

        <div className="flex items-center justify-between">
          <StarRating rating={book.avg_rating} size="sm" />
          <span
            className={`w-2 h-2 rounded-full flex-shrink-0 ${isAvailable ? 'bg-success' : 'bg-warning'}`}
            title={isAvailable ? 'Available' : 'Unavailable'}
          />
        </div>
      </div>
    </Link>
  );
}
