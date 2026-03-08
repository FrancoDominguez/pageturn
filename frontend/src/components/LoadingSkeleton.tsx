import { clsx } from 'clsx';

interface LoadingSkeletonProps {
  type: 'card' | 'table' | 'detail' | 'list';
  count?: number;
}

function Bone({ className }: { className?: string }) {
  return (
    <div className={clsx('animate-pulse rounded bg-gray-200', className)} />
  );
}

function CardSkeleton() {
  return (
    <div className="bg-surface rounded-card shadow-card overflow-hidden">
      <Bone className="aspect-[2/3] w-full rounded-none" />
      <div className="p-3 space-y-2">
        <Bone className="h-4 w-3/4" />
        <Bone className="h-3 w-1/2" />
        <Bone className="h-3 w-1/3" />
        <Bone className="h-5 w-20 rounded-pill" />
      </div>
    </div>
  );
}

function TableSkeleton() {
  return (
    <div className="bg-surface rounded-card shadow-card overflow-hidden">
      {/* Header */}
      <div className="flex items-center gap-4 px-4 py-3 border-b border-border">
        {[1, 2, 3, 4].map((i) => (
          <Bone key={i} className="h-3 flex-1" />
        ))}
      </div>
      {/* Rows */}
      {Array.from({ length: 5 }).map((_, i) => (
        <div key={i} className="flex items-center gap-4 px-4 py-3.5 border-b border-border last:border-0">
          <Bone className="h-10 w-8 rounded flex-shrink-0" />
          <div className="flex-1 space-y-1.5">
            <Bone className="h-3.5 w-2/3" />
            <Bone className="h-3 w-1/3" />
          </div>
          <Bone className="h-3 w-20" />
          <Bone className="h-7 w-16 rounded-button" />
        </div>
      ))}
    </div>
  );
}

function DetailSkeleton() {
  return (
    <div className="flex flex-col md:flex-row gap-8">
      <Bone className="w-full md:w-72 aspect-[2/3] rounded-card flex-shrink-0" />
      <div className="flex-1 space-y-4">
        <Bone className="h-8 w-3/4" />
        <Bone className="h-5 w-1/3" />
        <div className="flex gap-2">
          <Bone className="h-5 w-20 rounded-pill" />
          <Bone className="h-5 w-24 rounded-pill" />
        </div>
        <div className="space-y-2 pt-4">
          <Bone className="h-3.5 w-full" />
          <Bone className="h-3.5 w-full" />
          <Bone className="h-3.5 w-2/3" />
        </div>
        <div className="flex gap-3 pt-4">
          <Bone className="h-11 w-36 rounded-button" />
          <Bone className="h-11 w-36 rounded-button" />
        </div>
      </div>
    </div>
  );
}

function ListSkeleton() {
  return (
    <div className="space-y-3">
      {Array.from({ length: 4 }).map((_, i) => (
        <div key={i} className="flex items-center gap-4 bg-surface rounded-card shadow-card p-4">
          <Bone className="h-16 w-12 rounded flex-shrink-0" />
          <div className="flex-1 space-y-1.5">
            <Bone className="h-4 w-2/3" />
            <Bone className="h-3 w-1/3" />
          </div>
          <Bone className="h-6 w-20 rounded-pill" />
        </div>
      ))}
    </div>
  );
}

export default function LoadingSkeleton({ type, count = 1 }: LoadingSkeletonProps) {
  if (type === 'card') {
    return (
      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
        {Array.from({ length: count }).map((_, i) => (
          <CardSkeleton key={i} />
        ))}
      </div>
    );
  }

  if (type === 'table') {
    return <TableSkeleton />;
  }

  if (type === 'detail') {
    return <DetailSkeleton />;
  }

  return <ListSkeleton />;
}
