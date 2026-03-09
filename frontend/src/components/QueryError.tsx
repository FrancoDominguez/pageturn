interface QueryErrorProps {
  message?: string;
  onRetry?: () => void;
}

export default function QueryError({ message, onRetry }: QueryErrorProps) {
  return (
    <div className="flex flex-col items-center justify-center py-12 px-4 text-center">
      <div className="w-10 h-10 rounded-full bg-red-50 flex items-center justify-center mb-3">
        <svg className="w-5 h-5 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 9v2m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      </div>
      <p className="text-sm text-gray-500 mb-3">{message || 'Failed to load data.'}</p>
      {onRetry && (
        <button
          type="button"
          onClick={onRetry}
          className="px-3 py-1.5 text-sm font-medium text-primary hover:bg-primary/5 rounded-[6px] transition-colors cursor-pointer"
        >
          Retry
        </button>
      )}
    </div>
  );
}
