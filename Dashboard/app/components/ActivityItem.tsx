// app/components/ActivityItem.tsx
import { styles } from '../utils/styles';
import type { PlatformActivity } from '../types/admin';

interface ActivityItemProps {
  item: PlatformActivity;
}

export function ActivityItem({ item }: ActivityItemProps) {
  return (
    <div className="flex gap-3">
      <div
        className={`w-9 h-9 rounded-xl ${styles.flexCenter} text-base flex-shrink-0 ${
          item.type === 'alert'
            ? 'bg-red-500/10'
            : item.type === 'session'
              ? 'bg-brand/10'
              : 'bg-[#0bda62]/10'
        }`}
      >
        {item.icon}
      </div>
      <div>
        <p
          className={`text-sm font-bold ${
            item.type === 'alert' ? 'text-red-400' : 'text-white'
          }`}
        >
          {item.title}
        </p>
        <p className="text-[#d9d9d9] text-xs leading-relaxed">{item.desc}</p>
        <p className="text-[#aeb4a8] text-xs mt-1">{item.time}</p>
      </div>
    </div>
  );
}
