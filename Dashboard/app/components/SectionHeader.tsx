import type { ReactNode } from 'react';
import { styles } from '../utils/styles';

interface SectionHeaderProps {
  title: string;
  subtitle?: string;
  action?: ReactNode;
  className?: string;
}

export function SectionHeader({
  title,
  subtitle,
  action,
  className = 'mb-8',
}: SectionHeaderProps) {
  return (
    <div className={`${styles.flexBetween} items-start ${className}`}>
      <div>
        <h1 className={styles.pageTitle}>{title}</h1>
        {subtitle && <p className={styles.pageSubtitle}>{subtitle}</p>}
      </div>
      {action && <div>{action}</div>}
    </div>
  );
}
