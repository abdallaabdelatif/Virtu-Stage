const scenarioStyles: Record<string, string> = {
  'Job Interview': 'bg-brand/20 text-brand-soft',
  'Keynote Speech': 'bg-[#d9d9d9]/10 text-[#d9d9d9]',
  'Executive Meeting': 'bg-orange-500/20 text-orange-400',
  'Public Speaking': 'bg-[#0bda62]/20 text-[#0bda62]',
};

export function ScenarioBadge({ scenario }: { scenario: string }) {
  return (
    <span
      className={`px-3 py-1 rounded-lg text-xs font-bold ${scenarioStyles[scenario] ?? 'bg-[#2a3325] text-[#d9d9d9]'}`}
    >
      {scenario}
    </span>
  );
}
