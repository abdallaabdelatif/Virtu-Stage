interface CardProps {
  children: React.ReactNode;
  className?: string;
  title?: string;
  action?: React.ReactNode;
}

export function Card({ children, className = '', title, action }: CardProps) {
  return (
    <div
      className={`bg-[#1a2117] border border-[#46513c] rounded-2xl p-6 ${className}`}
    >
      {(title || action) && (
        <div className="flex items-center justify-between mb-5">
          {title && <h2 className="text-lg font-black text-white">{title}</h2>}
          {action}
        </div>
      )}
      {children}
    </div>
  );
}

interface StatCardProps {
  label: string;
  value: string;
  description?: string;
  color?: string;
  icon?: React.ReactNode;
  progress?: number;
  valueTone?: 'positive' | 'negative' | 'neutral';
}

export function StatCard({
  label,
  value,
  description,
  color = '#c1ff72',
  icon,
  progress,
  valueTone = 'neutral',
}: StatCardProps) {
  const valueToneClass =
    valueTone === 'positive'
      ? 'text-[#0bda62]'
      : valueTone === 'negative'
        ? 'text-red-400'
        : 'text-white';
  const boundedProgress =
    progress == null ? null : Math.min(100, Math.max(0, progress));
  return (
    <div className="bg-[#1a2117] border border-[#46513c] rounded-2xl p-5">
      <div className="flex justify-between items-start mb-3">
        <p className="text-[#d9d9d9] text-xs font-bold uppercase tracking-wider">
          {label}
        </p>
        {icon && (
          <span style={{ color }} className="opacity-80">
            {icon}
          </span>
        )}
      </div>
      <p className={`${valueToneClass} text-3xl font-black`}>{value}</p>
      {description && (
        <span className="mt-1 inline-block text-xs font-bold text-[#aeb4a8]">
          {description}
        </span>
      )}
      {boundedProgress != null && (
        <div className="w-full h-1 rounded-full mt-3 bg-[#2a3325]">
          <div
            role="progressbar"
            aria-label={`${label} progress`}
            aria-valuemin={0}
            aria-valuemax={100}
            aria-valuenow={boundedProgress}
            className="h-full rounded-full"
            style={{ width: `${boundedProgress}%`, backgroundColor: color }}
          />
        </div>
      )}
    </div>
  );
}
