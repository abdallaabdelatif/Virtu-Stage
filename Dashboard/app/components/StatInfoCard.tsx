// app/components/StatInfoCard.tsx
import type { ReactNode } from 'react';
import { styles } from '../utils/styles';

interface StatInfoCardProps {
  label: string;
  value: ReactNode;
  className?: string;
}

export function StatInfoCard({
  label,
  value,
  className = '',
}: StatInfoCardProps) {
  return (
    <div className={`${styles.cardSub} ${className}`}>
      <p className={`${styles.labelMuted} mb-1`}>{label}</p>
      <p className="text-white font-bold text-sm flex items-center gap-1">
        {value}
      </p>
    </div>
  );
}
