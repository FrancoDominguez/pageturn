import { useState } from 'react';
import { clsx } from 'clsx';

interface CoverImageProps {
  src?: string;
  title: string;
  author: string;
  className?: string;
}

function GradientPlaceholder({ title, author, className }: { title: string; author: string; className?: string }) {
  return (
    <div
      className={clsx(
        'flex flex-col items-center justify-center p-4 bg-gradient-to-br from-primary to-secondary',
        className,
      )}
    >
      <span className="text-white font-heading font-semibold text-center text-sm leading-tight line-clamp-3">
        {title}
      </span>
      <span className="text-white/80 text-xs text-center mt-1.5 line-clamp-1">
        {author}
      </span>
    </div>
  );
}

export default function CoverImage({ src, title, author, className }: CoverImageProps) {
  const [failed, setFailed] = useState(false);

  if (!src || failed) {
    return <GradientPlaceholder title={title} author={author} className={className} />;
  }

  return (
    <img
      src={src}
      alt={`Cover of ${title}`}
      className={clsx('object-cover', className)}
      onError={() => setFailed(true)}
      loading="lazy"
    />
  );
}
