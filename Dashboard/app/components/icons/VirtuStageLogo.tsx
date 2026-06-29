interface VirtuStageLogoProps {
  className?: string;
}

export function VirtuStageLogo({ className }: VirtuStageLogoProps) {
  return (
    <img src="/VirtuStage_logo.svg" className={className} alt="VirtuStage" />
  );
}
