import { useMyFines } from '../hooks/useFines';
import LoadingSkeleton from '../components/LoadingSkeleton';
import EmptyState from '../components/EmptyState';

// ── Reason pill ────────────────────────────────────────────────────────────

function ReasonPill({ reason }: { reason: string }) {
  const map: Record<string, { label: string; classes: string }> = {
    late_return: { label: 'Late Return', classes: 'bg-amber-50 text-amber-700' },
    lost_item: { label: 'Lost Item', classes: 'bg-red-50 text-red-700' },
    damaged_item: { label: 'Damaged', classes: 'bg-orange-50 text-orange-700' },
  };
  const config = map[reason] ?? { label: reason, classes: 'bg-gray-100 text-gray-700' };

  return (
    <span className={`inline-flex items-center px-2.5 py-1 rounded-pill text-xs font-medium ${config.classes}`}>
      {config.label}
    </span>
  );
}

// ── Status pill ────────────────────────────────────────────────────────────

function FineStatusPill({ status }: { status: string }) {
  const map: Record<string, { label: string; classes: string }> = {
    pending: { label: 'Pending', classes: 'bg-amber-50 text-amber-700' },
    paid: { label: 'Paid', classes: 'bg-emerald-50 text-emerald-700' },
    waived: { label: 'Waived', classes: 'bg-blue-50 text-blue-700' },
  };
  const config = map[status] ?? { label: status, classes: 'bg-gray-100 text-gray-700' };

  return (
    <span className={`inline-flex items-center px-2.5 py-1 rounded-pill text-xs font-medium ${config.classes}`}>
      {config.label}
    </span>
  );
}

// ── Main Page ──────────────────────────────────────────────────────────────

export default function FinesPage() {
  const { data, isLoading } = useMyFines();

  if (isLoading) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 py-8">
        <h1 className="font-heading font-bold text-2xl text-text-primary mb-6">Fines & Dues</h1>
        <LoadingSkeleton type="table" />
      </div>
    );
  }

  const fines = data?.fines ?? [];
  const totalOutstanding = data?.total_outstanding ?? 0;
  const checkoutBlocked = data?.checkout_blocked ?? false;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 py-8">
      <h1 className="font-heading font-bold text-2xl text-text-primary mb-6">Fines & Dues</h1>

      {/* Outstanding balance */}
      <div className="bg-surface rounded-card shadow-card p-6 mb-6">
        <p className="text-sm text-text-muted uppercase tracking-wider mb-1">Outstanding Balance</p>
        <p
          className={`font-heading text-4xl font-bold ${
            totalOutstanding > 0 ? 'text-primary' : 'text-success'
          }`}
        >
          ${totalOutstanding.toFixed(2)}
        </p>
      </div>

      {/* Warning banner */}
      {checkoutBlocked && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-card text-sm text-red-800">
          <strong>Checkout blocked.</strong> Your outstanding fines are $10.00 or more. Please pay your fines at the front desk before checking out new books.
        </div>
      )}

      {/* Fines table */}
      {fines.length === 0 ? (
        <EmptyState
          title="No fines"
          description="You're all clear! Keep up the good habit of returning books on time."
          icon={
            <svg className="w-12 h-12" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
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
                  <th className="px-4 py-3 font-medium">Reason</th>
                  <th className="px-4 py-3 font-medium">Amount</th>
                  <th className="px-4 py-3 font-medium">Status</th>
                  <th className="px-4 py-3 font-medium text-right">Date</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {fines.map((fine) => (
                  <tr key={fine.id} className="hover:bg-gray-50/50 transition-colors">
                    <td className="px-4 py-3">
                      <div className="min-w-0">
                        <p className="text-sm font-medium text-text-primary truncate">
                          {fine.book_title}
                        </p>
                        <p className="text-xs text-text-muted truncate">{fine.book_author}</p>
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <ReasonPill reason={fine.reason} />
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className={`text-sm font-semibold ${
                          fine.status === 'pending' ? 'text-primary' : 'text-text-muted'
                        }`}
                      >
                        ${fine.amount.toFixed(2)}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <FineStatusPill status={fine.status} />
                    </td>
                    <td className="px-4 py-3 text-right text-sm text-text-secondary">
                      {new Date(fine.created_at).toLocaleDateString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Payment info */}
      {fines.length > 0 && (
        <div className="mt-8 p-4 bg-blue-50 border border-blue-200 rounded-card text-sm text-blue-800">
          <strong>How to pay:</strong> Visit the library front desk during business hours to settle outstanding fines. We accept cash, credit/debit cards, and library account credit.
        </div>
      )}
    </div>
  );
}
