interface CustomTooltipProps {
  active?: boolean;
  payload?: Array<{ name: string; value: number; color: string }>;
  label?: string | number;
  labelFormatter?: (label: string | number) => string;
}

export const CustomTooltip = ({
  active,
  payload,
  label,
  labelFormatter,
}: CustomTooltipProps) => {
  if (active && payload && payload.length) {
    const displayLabel =
      label != null && labelFormatter ? labelFormatter(label) : label;
    return (
      <div className="bg-[#1a2117] border border-[#46513c] rounded-xl p-3 text-sm">
        <p className="text-[#d9d9d9] mb-1">{displayLabel}</p>
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
