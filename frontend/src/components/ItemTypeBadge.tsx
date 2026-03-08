const typeConfig: Record<string, { label: string; icon: string }> = {
  audiobook: { label: 'Audiobook', icon: '🎧' },
  dvd: { label: 'DVD', icon: '💿' },
  ebook: { label: 'E-Book', icon: '📱' },
  magazine: { label: 'Magazine', icon: '📰' },
};

interface ItemTypeBadgeProps {
  itemType: string;
}

export default function ItemTypeBadge({ itemType }: ItemTypeBadgeProps) {
  const config = typeConfig[itemType];

  // Don't render for regular books
  if (!config) return null;

  return (
    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-pill bg-gray-100 text-gray-600 text-xs font-medium">
      <span className="text-[10px]">{config.icon}</span>
      {config.label}
    </span>
  );
}
