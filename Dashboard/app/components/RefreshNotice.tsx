import { AlertCircle } from 'lucide-react';

interface RefreshNoticeProps {
  messages: string[];
}

export function RefreshNotice({ messages }: RefreshNoticeProps) {
  if (messages.length === 0) return null;

  return (
    <div
      role="status"
      aria-live="polite"
      className="mb-6 rounded-xl border border-brand/25 bg-brand/10 p-4"
    >
      <div className="flex items-start gap-3">
        <AlertCircle className="mt-0.5 h-5 w-5 flex-shrink-0 text-brand" />
        <div className="space-y-1">
          {messages.map((message, index) => (
            <p key={index} className="text-sm font-bold text-[#d9d9d9]">
              {message}
            </p>
          ))}
        </div>
      </div>
    </div>
  );
}
