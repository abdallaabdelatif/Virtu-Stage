// app/components/FeedbackItem.tsx
import { CheckCircle, AlertTriangle } from 'lucide-react';
import { styles } from '../utils/styles';

interface FeedbackItemProps {
  title: string;
  desc: string;
  reasons?: string[];
  type: 'strength' | 'growth';
}

export function FeedbackItem({
  title,
  desc,
  reasons,
  type,
}: FeedbackItemProps) {
  const isStrength = type === 'strength';
  const colorClass = isStrength ? 'text-[#0bda62]' : 'text-orange-400';
  const bgClass = isStrength ? 'bg-[#0bda62]/5' : 'bg-orange-400/5';
  const borderClass = isStrength
    ? 'border-[#0bda62]/10'
    : 'border-orange-400/10';

  return (
    <div
      className={`p-4 rounded-xl ${bgClass} border ${borderClass} flex gap-3`}
    >
      {isStrength ? (
        <CheckCircle className={`w-5 h-5 ${colorClass} flex-shrink-0 mt-0.5`} />
      ) : (
        <AlertTriangle
          className={`w-5 h-5 ${colorClass} flex-shrink-0 mt-0.5`}
        />
      )}
      <div>
        <p className="text-white font-bold text-base">{title}</p>
        <p
          className={`${styles.textMuted} mt-1 text-sm leading-relaxed sm:text-base`}
        >
          {desc}
        </p>
        {reasons && reasons.length > 0 && (
          <ul className="mt-2 space-y-1.5 text-sm leading-relaxed text-[#b8c0b0] sm:text-base">
            {reasons.map((reason) => (
              <li key={reason} className="flex gap-2">
                <span className={colorClass}>•</span>
                <span>{reason}</span>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
