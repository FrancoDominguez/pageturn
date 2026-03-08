import { clsx } from 'clsx';

interface AvailabilityBadgeProps {
  availableCopies: number;
  totalCopies: number;
  userHasBook?: boolean;
  isOverdue?: boolean;
}

export default function AvailabilityBadge({
  availableCopies,
  totalCopies,
  userHasBook,
  isOverdue,
}: AvailabilityBadgeProps) {
  let label: string;
  let dotColor: string;
  let bgColor: string;
  let textColor: string;

  if (isOverdue) {
    label = 'Overdue';
    dotColor = 'bg-red-500';
    bgColor = 'bg-red-50';
    textColor = 'text-red-700';
  } else if (userHasBook) {
    label = 'You have this book';
    dotColor = 'bg-blue-500';
    bgColor = 'bg-blue-50';
    textColor = 'text-blue-700';
  } else if (availableCopies > 0) {
    label = totalCopies > 1 ? `${availableCopies} of ${totalCopies} copies` : 'Available';
    dotColor = 'bg-success';
    bgColor = 'bg-emerald-50';
    textColor = 'text-emerald-700';
  } else {
    label = 'All copies out';
    dotColor = 'bg-warning';
    bgColor = 'bg-amber-50';
    textColor = 'text-amber-700';
  }

  return (
    <span
      className={clsx(
        'inline-flex items-center gap-1.5 px-2.5 py-1 rounded-pill text-xs font-medium',
        bgColor,
        textColor,
      )}
    >
      <span className={clsx('w-1.5 h-1.5 rounded-full flex-shrink-0', dotColor)} />
      {label}
    </span>
  );
}
