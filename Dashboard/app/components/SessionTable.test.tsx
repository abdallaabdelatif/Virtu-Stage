import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { SessionTable } from './SessionTable';
import type { SessionListItem } from '../types/session';

const sessions: SessionListItem[] = Array.from({ length: 6 }, (_, index) => ({
  id: `session-${index + 1}`,
  date: `Jun ${index + 1}, 2026`,
  time: '10:00 AM',
  scenario: index % 2 === 0 ? 'Job Interview' : 'Public Speaking',
  score: 80 + index,
  status: 'Completed',
  backendStatus: 'completed',
}));

describe('SessionTable', () => {
  it('opens completed sessions from a keyboard-operable row', () => {
    const onRowClick = vi.fn();
    render(
      <SessionTable
        sessions={sessions}
        actionLabel="View Analysis"
        onRowClick={onRowClick}
      />,
    );

    fireEvent.click(
      screen.getByRole('button', { name: /job interview session from jun 1/i }),
    );
    expect(onRowClick).toHaveBeenCalledWith('session-1');
  });

  it('filters scenarios and keeps pagination bounded', () => {
    render(
      <SessionTable
        sessions={sessions}
        actionLabel="View Analysis"
        onRowClick={vi.fn()}
      />,
    );

    fireEvent.change(screen.getByLabelText('Filter by scenario'), {
      target: { value: 'Public Speaking' },
    });
    expect(
      screen.getAllByRole('button', { name: /public speaking session/i }),
    ).toHaveLength(3);
    expect(
      screen.queryByRole('button', { name: 'Page 2' }),
    ).not.toBeInTheDocument();
  });
});
