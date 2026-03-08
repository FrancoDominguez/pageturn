import { Link } from 'react-router-dom';

interface EmptyStateProps {
  icon?: React.ReactNode;
  title: string;
  description?: string;
  action?: { label: string; href: string };
}

export default function EmptyState({ icon, title, description, action }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-16 px-4 text-center">
      {icon && (
        <div className="text-text-muted mb-4 text-5xl">
          {icon}
        </div>
      )}
      <h3 className="font-heading font-semibold text-lg text-text-primary mb-1">
        {title}
      </h3>
      {description && (
        <p className="text-text-muted text-sm max-w-sm mb-6">
          {description}
        </p>
      )}
      {action && (
        <Link
          to={action.href}
          className="inline-flex items-center px-5 py-2.5 bg-primary hover:bg-primary-hover text-white text-sm font-medium rounded-button transition-colors"
        >
          {action.label}
        </Link>
      )}
    </div>
  );
}
