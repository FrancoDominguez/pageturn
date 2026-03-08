import { Link } from 'react-router-dom';
import { useMyLoans, useMyReservations, useRenewLoan, useCancelReservation } from '../hooks/useLoans';
import CoverImage from '../components/CoverImage';
import LoadingSkeleton from '../components/LoadingSkeleton';
import EmptyState from '../components/EmptyState';
import { useToast } from '../components/Toast';

// ── Status pill ────────────────────────────────────────────────────────────

function StatusPill({ status, daysRemaining }: { status: string; daysRemaining: number }) {
  let label: string;
  let classes: string;

  if (status === 'overdue') {
    label = 'Overdue';
    classes = 'bg-red-50 text-red-700';
  } else if (daysRemaining <= 3) {
    label = 'Due Soon';
    classes = 'bg-amber-50 text-amber-700';
  } else {
    label = 'Active';
    classes = 'bg-emerald-50 text-emerald-700';
  }

  return (
    <span className={`inline-flex items-center px-2.5 py-1 rounded-pill text-xs font-medium ${classes}`}>
      {label}
    </span>
  );
}

// ── Reservation status pill ────────────────────────────────────────────────

function ReservationStatusPill({ status }: { status: string }) {
  const map: Record<string, { label: string; classes: string }> = {
    pending: { label: 'Waiting', classes: 'bg-gray-100 text-gray-700' },
    ready: { label: 'Ready for Pickup', classes: 'bg-emerald-50 text-emerald-700' },
    fulfilled: { label: 'Fulfilled', classes: 'bg-blue-50 text-blue-700' },
    expired: { label: 'Expired', classes: 'bg-red-50 text-red-700' },
    cancelled: { label: 'Cancelled', classes: 'bg-gray-100 text-gray-500' },
  };
  const config = map[status] ?? { label: status, classes: 'bg-gray-100 text-gray-700' };

  return (
    <span className={`inline-flex items-center px-2.5 py-1 rounded-pill text-xs font-medium ${config.classes}`}>
      {config.label}
    </span>
  );
}

// ── Main Page ──────────────────────────────────────────────────────────────

export default function LoansPage() {
  const { data: loansData, isLoading: loansLoading } = useMyLoans();
  const { data: reservationsData, isLoading: reservationsLoading } = useMyReservations();
  const renewLoan = useRenewLoan();
  const cancelReservation = useCancelReservation();
  const { toast } = useToast();

  const loans = loansData?.loans ?? [];
  const reservations = reservationsData?.reservations ?? [];

  const overdueLoans = loans.filter((l) => l.status === 'overdue');
  const readyReservations = reservations.filter((r) => r.status === 'ready');

  const handleRenew = (loanId: string) => {
    renewLoan.mutate(loanId, {
      onSuccess: () => toast('Loan renewed successfully!', 'success'),
      onError: (err) => toast(err.message || 'Failed to renew loan.', 'error'),
    });
  };

  const handleCancelReservation = (id: string) => {
    cancelReservation.mutate(id, {
      onSuccess: () => toast('Reservation cancelled.', 'success'),
      onError: (err) => toast(err.message || 'Failed to cancel reservation.', 'error'),
    });
  };

  if (loansLoading) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 py-8">
        <h1 className="font-heading font-bold text-2xl text-text-primary mb-6">My Loans</h1>
        <LoadingSkeleton type="table" />
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 py-8">
      <h1 className="font-heading font-bold text-2xl text-text-primary mb-6">My Loans</h1>

      {/* Ready reservation alert */}
      {readyReservations.length > 0 && (
        <div className="mb-6 p-4 bg-emerald-50 border border-emerald-200 rounded-card text-sm text-emerald-800">
          <strong>Reservation ready!</strong> {readyReservations.length === 1
            ? `"${readyReservations[0].book.title}" is ready for pickup.`
            : `${readyReservations.length} reservations are ready for pickup.`}
        </div>
      )}

      {/* Overdue alert */}
      {overdueLoans.length > 0 && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-card text-sm text-red-800">
          <strong>Overdue!</strong> You have {overdueLoans.length} overdue {overdueLoans.length === 1 ? 'loan' : 'loans'}. Fines may be accruing at $0.25/day per book.
        </div>
      )}

      {/* Loans table */}
      {loans.length === 0 ? (
        <EmptyState
          title="No active loans"
          description="Browse the library to find your next read."
          action={{ label: 'Browse Library', href: '/' }}
          icon={
            <svg className="w-12 h-12" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
            </svg>
          }
        />
      ) : (
        <div className="bg-surface rounded-card shadow-card overflow-hidden">
          {/* Desktop table */}
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="bg-[#0d1117] text-white text-left text-sm">
                  <th className="px-4 py-3 font-medium">Book</th>
                  <th className="px-4 py-3 font-medium hidden sm:table-cell">Checked Out</th>
                  <th className="px-4 py-3 font-medium">Due Date</th>
                  <th className="px-4 py-3 font-medium">Status</th>
                  <th className="px-4 py-3 font-medium hidden md:table-cell">Renewals</th>
                  <th className="px-4 py-3 font-medium text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {loans.map((loan) => (
                  <tr key={loan.id} className="hover:bg-gray-50/50 transition-colors">
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
                    <td className="px-4 py-3">
                      <div>
                        <p className="text-sm text-text-primary">{new Date(loan.due_date).toLocaleDateString()}</p>
                        <p className={`text-xs ${loan.status === 'overdue' ? 'text-red-600 font-medium' : 'text-text-muted'}`}>
                          {loan.status === 'overdue'
                            ? `${loan.days_overdue ?? 0} days overdue`
                            : `${loan.days_remaining} days remaining`}
                        </p>
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <StatusPill status={loan.status} daysRemaining={loan.days_remaining} />
                    </td>
                    <td className="px-4 py-3 text-sm text-text-secondary hidden md:table-cell">
                      {loan.renewed_count}/3
                    </td>
                    <td className="px-4 py-3 text-right">
                      {loan.can_renew ? (
                        <button
                          type="button"
                          onClick={() => handleRenew(loan.id)}
                          disabled={renewLoan.isPending}
                          className="text-sm font-medium text-primary hover:text-primary-hover transition-colors cursor-pointer disabled:opacity-50"
                        >
                          Renew
                        </button>
                      ) : (
                        <span className="text-xs text-text-muted">
                          {loan.renewal_blocked_reason || 'Cannot renew'}
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Reservations section */}
      {!reservationsLoading && reservations.length > 0 && (
        <section className="mt-10">
          <h2 className="font-heading font-semibold text-xl text-text-primary mb-4">Reservations</h2>
          <div className="bg-surface rounded-card shadow-card overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="bg-gray-50 text-left text-sm">
                    <th className="px-4 py-3 font-medium text-text-secondary">Book</th>
                    <th className="px-4 py-3 font-medium text-text-secondary">Reserved</th>
                    <th className="px-4 py-3 font-medium text-text-secondary">Status</th>
                    <th className="px-4 py-3 font-medium text-text-secondary">Queue</th>
                    <th className="px-4 py-3 font-medium text-text-secondary text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {reservations.map((res) => (
                    <tr key={res.id} className="hover:bg-gray-50/50 transition-colors">
                      <td className="px-4 py-3">
                        <Link to={`/books/${res.book.id}`} className="flex items-center gap-3 group">
                          <CoverImage
                            src={res.book.cover_image_url}
                            title={res.book.title}
                            author={res.book.author}
                            className="w-10 h-14 rounded flex-shrink-0 object-cover"
                          />
                          <div className="min-w-0">
                            <p className="text-sm font-medium text-text-primary truncate group-hover:text-primary transition-colors">
                              {res.book.title}
                            </p>
                            <p className="text-xs text-text-muted truncate">{res.book.author}</p>
                          </div>
                        </Link>
                      </td>
                      <td className="px-4 py-3 text-sm text-text-secondary">
                        {new Date(res.reserved_at).toLocaleDateString()}
                      </td>
                      <td className="px-4 py-3">
                        <ReservationStatusPill status={res.status} />
                      </td>
                      <td className="px-4 py-3 text-sm text-text-secondary">
                        {res.queue_position != null ? `#${res.queue_position}` : '-'}
                      </td>
                      <td className="px-4 py-3 text-right">
                        {(res.status === 'pending' || res.status === 'ready') && (
                          <button
                            type="button"
                            onClick={() => handleCancelReservation(res.id)}
                            disabled={cancelReservation.isPending}
                            className="text-sm font-medium text-red-600 hover:text-red-700 transition-colors cursor-pointer disabled:opacity-50"
                          >
                            Cancel
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </section>
      )}

      {/* Return info banner */}
      {loans.length > 0 && (
        <div className="mt-8 p-4 bg-blue-50 border border-blue-200 rounded-card text-sm text-blue-800">
          <strong>Returning a book?</strong> Visit the library front desk during operating hours. Books can also be returned via the book drop outside.
        </div>
      )}
    </div>
  );
}
