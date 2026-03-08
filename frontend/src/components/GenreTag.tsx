import { clsx } from 'clsx';

interface GenreTagProps {
  genre: string;
  onClick?: () => void;
}

/**
 * Deterministic color selection based on the genre string.
 * Alternates between coral and blue variants.
 */
function getGenreStyle(genre: string): { bg: string; text: string } {
  const hash = genre.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0);
  return hash % 2 === 0
    ? { bg: 'bg-red-50', text: 'text-primary' }
    : { bg: 'bg-sky-50', text: 'text-secondary' };
}

export default function GenreTag({ genre, onClick }: GenreTagProps) {
  const style = getGenreStyle(genre);

  return (
    <button
      type="button"
      onClick={onClick}
      disabled={!onClick}
      className={clsx(
        'inline-flex items-center px-2.5 py-0.5 rounded-pill text-xs font-medium transition-colors',
        style.bg,
        style.text,
        onClick
          ? 'cursor-pointer hover:opacity-80'
          : 'cursor-default',
      )}
    >
      {genre}
    </button>
  );
}
