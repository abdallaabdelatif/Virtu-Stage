// app/components/CustomTooltip.tsx

interface CustomTooltipProps {
  active?: boolean;
  payload?: Array<{ name: string; value: number; color: string }>;
  label?: string;
}

export const CustomTooltip = ({ active, payload, label }: CustomTooltipProps) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-[#1b1d28] border border-[#393f56] rounded-xl p-3 text-sm">
        <p className="text-[#9aa1bc] mb-1">{label}</p>
        {payload.map((p) => (
          <p key={p.name} style={{ color: p.color }} className="font-bold">
            {p.name}: {p.value}
          </p>
        ))}
      </div>
    );
  }
  return null;
};
