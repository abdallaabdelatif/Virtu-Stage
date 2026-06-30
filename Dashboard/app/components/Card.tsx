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

// Stat card variant
interface StatCardProps {
  label: string;
  value: string;
  change?: string;
  color?: string;
  icon?: React.ReactNode;
}

export function StatCard({
  label,
  value,
  change,
  color = '#c1ff72',
  icon,
}: StatCardProps) {
  const isPositive = change?.startsWith('+');
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
      <p className="text-white text-3xl font-black">{value}</p>
      {change && (
        <span
          className={`text-xs font-bold mt-1 inline-block ${isPositive ? 'text-[#0bda62]' : 'text-red-400'}`}
        >
          {change} from last month
        </span>
      )}
      <div className="w-full h-1 rounded-full mt-3 bg-[#2a3325]">
        <div
          className="h-full rounded-full"
          style={{ width: '60%', backgroundColor: color }}
        />
      </div>
    </div>
  );
}
