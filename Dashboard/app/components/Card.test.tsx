import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { StatCard } from './Card';

describe('StatCard', () => {
  it('shows truthful descriptions and data-driven progress', () => {
    render(
      <StatCard
        label="Average Score"
        value="82/100"
        description="Average across completed sessions"
        progress={82}
      />,
    );

    expect(screen.getByText('Average across completed sessions')).toBeVisible();
    expect(screen.queryByText(/from last month/i)).not.toBeInTheDocument();
    expect(screen.getByRole('progressbar')).toHaveAttribute(
      'aria-valuenow',
      '82',
    );
    expect(screen.getByRole('progressbar')).toHaveStyle({ width: '82%' });
  });

  it('omits progress when the metric has no meaningful maximum', () => {
    render(
      <StatCard
        label="Total Sessions"
        value="12"
        description="Your recorded training sessions"
      />,
    );

    expect(screen.queryByRole('progressbar')).not.toBeInTheDocument();
  });
});
