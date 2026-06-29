// app/components/FeedbackItem.tsx
import { CheckCircle, AlertTriangle } from 'lucide-react';
import { styles } from '../utils/styles';

interface FeedbackItemProps {
  title: string;
  desc: string;
  type: "strength" | "growth";
}

export function FeedbackItem({ title, desc, type }: FeedbackItemProps) {
  const isStrength = type === "strength";
  const colorClass = isStrength ? "text-[#0bda62]" : "text-orange-400";
  const bgClass = isStrength ? "bg-[#0bda62]/5" : "bg-orange-400/5";
  const borderClass = isStrength ? "border-[#0bda62]/10" : "border-orange-400/10";

  return (
    <div className={`p-4 rounded-xl ${bgClass} border ${borderClass} flex gap-3`}>
      {isStrength ? (
        <CheckCircle className={`w-5 h-5 ${colorClass} flex-shrink-0 mt-0.5`} />
      ) : (
        <AlertTriangle className={`w-5 h-5 ${colorClass} flex-shrink-0 mt-0.5`} />
      )}
      <div>
        <p className="text-white font-bold text-sm">{title}</p>
        <p className={`${styles.textMuted} mt-0.5 leading-relaxed`}>{desc}</p>
      </div>
    </div>
  );
}
