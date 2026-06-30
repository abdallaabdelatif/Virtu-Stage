import type { LucideIcon } from 'lucide-react';

interface EmptyStateProps {
  icon: LucideIcon;
  title: string;
  description: string;
  compact?: boolean;
}

export function EmptyState({
  icon: Icon,
  title,
  description,
  compact = false,
}: EmptyStateProps) {
  return (
    <section
      className={`flex flex-col items-center justify-center rounded-3xl border-2 border-dashed border-[#2a3325] bg-[#121610]/60 px-6 text-center ${
        compact ? 'py-8' : 'py-16'
      }`}
    >
      <div
        className={`mb-4 flex items-center justify-center rounded-2xl bg-brand/10 text-brand-soft ${
          compact ? 'h-12 w-12' : 'h-16 w-16'
        }`}
      >
        <Icon className={compact ? 'h-6 w-6' : 'h-8 w-8'} />
      </div>
      <h3 className="text-lg font-black text-white">{title}</h3>
      <p className="mt-2 max-w-md text-sm leading-relaxed text-[#aeb4a8]">
        {description}
      </p>
    </section>
  );
}
