// app/components/Toggle.tsx

interface ToggleProps {
  enabled: boolean;
  onChange: () => void;
}

export function Toggle({ enabled, onChange }: ToggleProps) {
  return (
    <button
      onClick={onChange}
      className={`relative w-12 h-6 rounded-full transition-colors shrink-0 ${
        enabled ? "bg-[#5c7cff]" : "bg-[#393f56]"
      }`}
    >
      <span
        className={`absolute left-0 top-1 w-4 h-4 rounded-full bg-white transition-transform ${
          enabled ? "translate-x-7" : "translate-x-1"
        }`}
      />
    </button>
  );
}
