import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { MemoryRouter } from 'react-router';
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

function renderTable(initialEntry = '/sessions') {
  return render(
    <MemoryRouter initialEntries={[initialEntry]}>
      <SessionTable
        sessions={sessions}
        actionLabel="View Analysis"
        onRowClick={vi.fn()}
      />
    </MemoryRouter>,
  );
}

describe('SessionTable', () => {
  it('opens completed sessions from a keyboard-operable row', () => {
    const onRowClick = vi.fn();
    render(
      <MemoryRouter>
        <SessionTable
          sessions={sessions}
          actionLabel="View Analysis"
          onRowClick={onRowClick}
        />
      </MemoryRouter>,
    );

    fireEvent.click(
      screen.getByRole('button', { name: /job interview session from jun 1/i }),
    );
    expect(onRowClick).toHaveBeenCalledWith('session-1');
  });

  it('filters scenarios and keeps pagination bounded', () => {
    renderTable();

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

  it('restores the selected page from the URL', () => {
    renderTable('/sessions?page=2');

    expect(
      screen.getByRole('button', { name: /job interview session from jun 5/i }),
    ).toBeInTheDocument();
    expect(
      screen.queryByRole('button', {
        name: /job interview session from jun 1/i,
      }),
    ).not.toBeInTheDocument();
  });
});
