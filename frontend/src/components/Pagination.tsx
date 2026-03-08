import { clsx } from 'clsx';

interface PaginationProps {
  page: number;
  pages: number;
  onPageChange: (page: number) => void;
}

/**
 * Builds the array of page numbers to display.
 * Shows first, last, current, and neighbors with ellipsis gaps.
 */
function getPageNumbers(current: number, total: number): (number | '...')[] {
  if (total <= 7) {
    return Array.from({ length: total }, (_, i) => i + 1);
  }

  const pages: (number | '...')[] = [];
  const left = Math.max(2, current - 1);
  const right = Math.min(total - 1, current + 1);

  pages.push(1);

  if (left > 2) pages.push('...');

  for (let i = left; i <= right; i++) {
    pages.push(i);
  }

  if (right < total - 1) pages.push('...');

  pages.push(total);

  return pages;
}

export default function Pagination({ page, pages, onPageChange }: PaginationProps) {
  if (pages <= 1) return null;

  const pageNumbers = getPageNumbers(page, pages);

  return (
    <nav className="flex items-center justify-center gap-1.5" aria-label="Pagination">
      <button
        type="button"
        onClick={() => onPageChange(page - 1)}
        disabled={page <= 1}
        className={clsx(
          'px-3.5 py-2 text-sm font-medium rounded-button transition-colors',
          page <= 1
            ? 'text-text-muted cursor-not-allowed'
            : 'text-text-secondary hover:bg-gray-100 cursor-pointer',
        )}
      >
        Previous
      </button>

      {pageNumbers.map((num, idx) =>
        num === '...' ? (
          <span key={`ellipsis-${idx}`} className="px-2 py-2 text-sm text-text-muted">
            ...
          </span>
        ) : (
          <button
            key={num}
            type="button"
            onClick={() => onPageChange(num)}
            className={clsx(
              'w-9 h-9 flex items-center justify-center text-sm font-medium rounded-full transition-colors cursor-pointer',
              num === page
                ? 'bg-primary text-white'
                : 'text-text-secondary hover:bg-gray-100',
            )}
            aria-current={num === page ? 'page' : undefined}
          >
            {num}
          </button>
        ),
      )}

      <button
        type="button"
        onClick={() => onPageChange(page + 1)}
        disabled={page >= pages}
        className={clsx(
          'px-3.5 py-2 text-sm font-medium rounded-button transition-colors',
          page >= pages
            ? 'text-text-muted cursor-not-allowed'
            : 'text-text-secondary hover:bg-gray-100 cursor-pointer',
        )}
      >
        Next
      </button>
    </nav>
  );
}
