// app/components/AnalyticsStatCard.tsx
import type { ReactNode } from 'react';
import { styles } from '../utils/styles';

interface AnalyticsStatCardProps {
  label: string;
  value: ReactNode;
  badgeText?: string;
  badgeType?: 'positive' | 'warning' | 'neutral';
  subText?: string;
  barProgress?: number;
}

export function AnalyticsStatCard({
  label,
  value,
  badgeText,
  badgeType,
  subText,
  barProgress
}: AnalyticsStatCardProps) {
  
  let badgeColorClass = "";
  if (badgeType === "positive") badgeColorClass = "text-[#0bda62] bg-[#0bda62]/10";
  if (badgeType === "warning") badgeColorClass = "text-orange-400 bg-orange-400/10";
  if (badgeType === "neutral") badgeColorClass = "text-[#5c6484] bg-[#5c6484]/10";

  return (
    <div className={styles.cardSub}>
      <div className={`${styles.flexBetween} items-start mb-2`}>
        <p className={styles.labelMuted}>{label}</p>
        {badgeText ? (
          <span className={`text-xs font-bold px-2 py-0.5 rounded ${badgeColorClass}`}>
            {badgeText}
          </span>
        ) : null}
      </div>
      
      {barProgress !== undefined ? (
        <>
          <div className="flex items-baseline gap-1 mt-2">
            <span className={styles.statValueLarge}>{value}</span>
            <span className="text-[#5c6484] text-xl font-bold">/100</span>
          </div>
          <div className="w-full h-2 bg-[#12141c] rounded-full mt-4">
            <div className="h-full bg-[#5c7cff] rounded-full" style={{ width: `${barProgress}%` }} />
          </div>
        </>
      ) : (
        <>
          <p className={`${styles.statValueLarge} mt-2`}>
            {value}
          </p>
          {subText && <p className={`${styles.textMuted} mt-auto pt-3`}>{subText}</p>}
        </>
      )}
    </div>
  );
}
