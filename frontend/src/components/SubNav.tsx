import { NavLink } from 'react-router-dom';
import { clsx } from 'clsx';

interface SubNavProps {
  fineAmount?: number;
}

const links = [
  { to: '/loans', label: 'Loans' },
  { to: '/history', label: 'History' },
  { to: '/fines', label: 'Fines', showBadge: true },
  { to: '/reviews', label: 'Reviews' },
  { to: '/ai-assistant', label: 'AI Assistant' },
];

export default function SubNav({ fineAmount }: SubNavProps) {
  return (
    <nav className="bg-surface border-b border-border">
      <div className="max-w-7xl mx-auto px-4 sm:px-6">
        <div className="flex items-center gap-1 overflow-x-auto scrollbar-hide -mb-px">
          {links.map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              className={({ isActive }) =>
                clsx(
                  'flex items-center gap-1.5 px-4 py-3 text-sm font-medium whitespace-nowrap border-b-[3px] transition-colors',
                  isActive
                    ? 'border-primary text-primary'
                    : 'border-transparent text-text-secondary hover:text-text-primary hover:border-gray-200',
                )
              }
            >
              {link.label}
              {link.showBadge && fineAmount !== undefined && fineAmount > 0 && (
                <span className="inline-flex items-center px-1.5 py-0.5 rounded-pill bg-primary text-white text-[10px] font-semibold leading-none">
                  ${Number(fineAmount).toFixed(2)}
                </span>
              )}
            </NavLink>
          ))}
        </div>
      </div>
    </nav>
  );
}
