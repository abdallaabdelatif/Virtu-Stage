interface VirtuStageLogoProps {
  className?: string;
  variant?: 'icon' | 'wordmark';
}

export function VirtuStageLogo({
  className,
  variant = 'icon',
}: VirtuStageLogoProps) {
  const src =
    variant === 'wordmark'
      ? '/virtustage-wordmark.png'
      : '/virtustage-icon.png';

  return (
    <img src={src} className={className} alt="VirtuStage" decoding="async" />
  );
}
