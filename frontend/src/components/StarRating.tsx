import { useState } from 'react';
import { clsx } from 'clsx';

interface StarRatingProps {
  rating: number;
  count?: number;
  size?: 'sm' | 'md' | 'lg';
  interactive?: boolean;
  onChange?: (rating: number) => void;
}

const sizeMap = {
  sm: 'w-3.5 h-3.5',
  md: 'w-5 h-5',
  lg: 'w-6 h-6',
};

function StarIcon({ filled, half, className }: { filled: boolean; half?: boolean; className?: string }) {
  if (half) {
    return (
      <svg className={className} viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
        <defs>
          <linearGradient id="halfGrad">
            <stop offset="50%" stopColor="#f59e0b" />
            <stop offset="50%" stopColor="transparent" />
          </linearGradient>
        </defs>
        <path
          d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z"
          fill="url(#halfGrad)"
          stroke="#f59e0b"
          strokeWidth="1"
        />
      </svg>
    );
  }

  return (
    <svg className={className} viewBox="0 0 20 20" fill={filled ? '#f59e0b' : 'none'} xmlns="http://www.w3.org/2000/svg">
      <path
        d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z"
        stroke="#f59e0b"
        strokeWidth={filled ? '0' : '1.5'}
      />
    </svg>
  );
}

export default function StarRating({ rating, count, size = 'md', interactive = false, onChange }: StarRatingProps) {
  const [hoverRating, setHoverRating] = useState(0);
  const displayRating = interactive && hoverRating > 0 ? hoverRating : rating;

  const stars = Array.from({ length: 5 }, (_, i) => {
    const starValue = i + 1;
    const filled = displayRating >= starValue;
    const half = !filled && displayRating >= starValue - 0.5;

    return (
      <button
        key={i}
        type="button"
        disabled={!interactive}
        className={clsx(
          'p-0 border-0 bg-transparent',
          interactive ? 'cursor-pointer' : 'cursor-default',
        )}
        onClick={() => interactive && onChange?.(starValue)}
        onMouseEnter={() => interactive && setHoverRating(starValue)}
        onMouseLeave={() => interactive && setHoverRating(0)}
        aria-label={`${starValue} star${starValue > 1 ? 's' : ''}`}
      >
        <StarIcon
          filled={filled}
          half={half}
          className={clsx(sizeMap[size], 'flex-shrink-0')}
        />
      </button>
    );
  });

  return (
    <div className="flex items-center gap-0.5">
      {stars}
      {count !== undefined && (
        <span className={clsx(
          'text-text-muted ml-1',
          size === 'sm' ? 'text-xs' : size === 'md' ? 'text-sm' : 'text-base',
        )}>
          ({count.toLocaleString()})
        </span>
      )}
    </div>
  );
}
