const scenarioStyles: Record<string, string> = {
  "Job Interview": "bg-[#5c7cff]/20 text-[#5c7cff]",
  "Keynote Speech": "bg-purple-500/20 text-purple-400",
  "Executive Meeting": "bg-orange-500/20 text-orange-400",
  "Public Speaking": "bg-[#0bda62]/20 text-[#0bda62]",
}

export function ScenarioBadge({ scenario }: { scenario: string }) {
  return (
    <span className={`px-3 py-1 rounded-lg text-xs font-bold ${scenarioStyles[scenario] ?? "bg-[#272b3a] text-[#9aa1bc]"}`}>
      {scenario}
    </span>
  )
}
