import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useLoanHistory } from '../hooks/useLoans';
import type { LoanHistory } from '../types';
import CoverImage from '../components/CoverImage';
import StarRating from '../components/StarRating';
import Pagination from '../components/Pagination';
import LoadingSkeleton from '../components/LoadingSkeleton';
import EmptyState from '../components/EmptyState';

// ── Group loans by month ───────────────────────────────────────────────────

function groupByMonth(loans: LoanHistory[]): [string, LoanHistory[]][] {
  const groups: Record<string, LoanHistory[]> = {};
  for (const loan of loans) {
    const date = new Date(loan.checked_out_at);
    const label = date.toLocaleDateString(undefined, { year: 'numeric', month: 'long' });
    if (!groups[label]) groups[label] = [];
    groups[label].push(loan);
  }
  return Object.entries(groups);
}

// ── Main Page ──────────────────────────────────────────────────────────────

export default function HistoryPage() {
  const [page, setPage] = useState(1);
  const { data, isLoading } = useLoanHistory(page);

  const loans = data?.loans ?? [];
  const monthGroups = groupByMonth(loans);

  // Find most recent unreviewed return for nudge
  const unreviewedReturn = loans.find((l) => l.returned_at && !l.user_review);

  if (isLoading) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 py-8">
        <h1 className="font-heading font-bold text-2xl text-text-primary mb-6">Borrowing History</h1>
        <LoadingSkeleton type="table" />
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 py-8">
      <h1 className="font-heading font-bold text-2xl text-text-primary mb-6">Borrowing History</h1>

      {/* Review nudge */}
      {unreviewedReturn && (
        <div className="mb-6 p-4 bg-amber-50 border border-amber-200 rounded-card text-sm text-amber-800 flex items-center justify-between gap-4">
          <div>
            <strong>How was "{unreviewedReturn.book.title}"?</strong> Share your thoughts by writing a review.
          </div>
          <Link
            to={`/books/${unreviewedReturn.book.id}`}
            className="text-sm font-medium text-primary hover:text-primary-hover transition-colors whitespace-nowrap"
          >
            Write Review
          </Link>
        </div>
      )}

      {loans.length === 0 ? (
        <EmptyState
          title="No borrowing history"
          description="Once you check out a book, it will appear here."
          action={{ label: 'Browse Library', href: '/' }}
          icon={
            <svg className="w-12 h-12" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          }
        />
      ) : (
        <div className="bg-surface rounded-card shadow-card overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="bg-[#0d1117] text-white text-left text-sm">
                  <th className="px-4 py-3 font-medium">Book</th>
                  <th className="px-4 py-3 font-medium hidden sm:table-cell">Borrowed</th>
                  <th className="px-4 py-3 font-medium hidden sm:table-cell">Returned</th>
                  <th className="px-4 py-3 font-medium">Action</th>
                  <th className="px-4 py-3 font-medium">Review</th>
                  <th className="px-4 py-3 font-medium text-right">Fine</th>
                </tr>
              </thead>
              <tbody>
                {monthGroups.map(([month, monthLoans]) => (
                  <MonthGroup key={month} month={month} loans={monthLoans} />
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Pagination */}
      {data && data.total > 20 && (
        <div className="mt-8">
          <Pagination
            page={page}
            pages={Math.ceil(data.total / 20)}
            onPageChange={setPage}
          />
        </div>
      )}
    </div>
  );
}

// ── Month group ────────────────────────────────────────────────────────────

function MonthGroup({ month, loans }: { month: string; loans: LoanHistory[] }) {
  return (
    <>
      <tr>
        <td colSpan={6} className="bg-gray-50 px-4 py-2">
          <span className="text-xs font-semibold text-text-muted uppercase tracking-wider">{month}</span>
        </td>
      </tr>
      {loans.map((loan) => (
        <tr key={loan.id} className="border-b border-border last:border-0 hover:bg-gray-50/50 transition-colors">
          <td className="px-4 py-3">
            <Link to={`/books/${loan.book.id}`} className="flex items-center gap-3 group">
              <CoverImage
                src={loan.book.cover_image_url}
                title={loan.book.title}
                author={loan.book.author}
                className="w-10 h-14 rounded flex-shrink-0 object-cover"
              />
              <div className="min-w-0">
                <p className="text-sm font-medium text-text-primary truncate group-hover:text-primary transition-colors">
                  {loan.book.title}
                </p>
                <p className="text-xs text-text-muted truncate">{loan.book.author}</p>
              </div>
            </Link>
          </td>
          <td className="px-4 py-3 text-sm text-text-secondary hidden sm:table-cell">
            {new Date(loan.checked_out_at).toLocaleDateString()}
          </td>
          <td className="px-4 py-3 text-sm text-text-secondary hidden sm:table-cell">
            {loan.returned_at ? new Date(loan.returned_at).toLocaleDateString() : '-'}
          </td>
          <td className="px-4 py-3">
            <Link
              to={`/books/${loan.book.id}`}
              className="text-sm font-medium text-primary hover:text-primary-hover transition-colors"
            >
              Borrow Again
            </Link>
          </td>
          <td className="px-4 py-3">
            {loan.user_review ? (
              <StarRating rating={loan.user_review.rating} size="sm" />
            ) : loan.returned_at ? (
              <Link
                to={`/books/${loan.book.id}`}
                className="text-sm font-medium text-secondary hover:opacity-80 transition-opacity"
              >
                Write Review
              </Link>
            ) : (
              <span className="text-xs text-text-muted">-</span>
            )}
          </td>
          <td className="px-4 py-3 text-right">
            {loan.was_late ? (
              <span className="text-sm text-red-600 font-medium">Late</span>
            ) : (
              <span className="text-sm text-text-muted">-</span>
            )}
          </td>
        </tr>
      ))}
    </>
  );
}
