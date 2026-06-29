// app/components/ScenarioToggleRow.tsx
import { styles } from '../utils/styles';
import type { TrainingScenario } from '../types/admin';
import { Toggle } from './Toggle';

interface ScenarioToggleRowProps {
  scenario: TrainingScenario;
  onToggle: (id: string) => void;
}

export function ScenarioToggleRow({ scenario, onToggle }: ScenarioToggleRowProps) {
  return (
    <div className={`${styles.flexBetween} gap-3 p-3 rounded-xl bg-[#12141c] border border-[#272b3a]`}>
      <span className={`text-sm font-bold ${scenario.enabled ? "text-white" : "text-[#5c6484]"}`}>
        {scenario.name}
      </span>
      <Toggle enabled={scenario.enabled} onChange={() => onToggle(scenario.id)} />
    </div>
  );
}
