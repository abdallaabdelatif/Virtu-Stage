import { useEffect, useMemo, useState } from 'react';
import { Search, ChevronLeft, ChevronRight } from 'lucide-react';
import { useSessionPolling } from '../hooks/useSessionPolling';
import { styles } from '../utils/styles';
import { StatusBadge } from './StatusBadge';
import { ScenarioBadge } from './ScenarioBadge';
import { ScoreProgressBar } from './ScoreBadge';
import type { SessionListItem } from '../types/session';

const ITEMS_PER_PAGE = 4;

interface SessionTableProps {
  sessions: SessionListItem[];
  actionLabel: string;
  onRowClick: (id: number | string) => void;
  onRefresh?: () => void;
}

function getVisiblePages(page: number, totalPages: number) {
  const start = Math.max(1, Math.min(page - 2, totalPages - 4));
  const end = Math.min(totalPages, start + 4);
  return Array.from(
    { length: Math.max(0, end - start + 1) },
    (_, index) => start + index,
  );
}

export function SessionTable({
  sessions,
  actionLabel,
  onRowClick,
  onRefresh,
}: SessionTableProps) {
  const [search, setSearch] = useState('');
  const [scenario, setScenario] = useState('All');
  const [page, setPage] = useState(1);

  const scenarios = useMemo(
    () =>
      Array.from(new Set(sessions.map((session) => session.scenario))).sort(),
    [sessions],
  );
  const normalizedSearch = search.trim().toLowerCase();
  const filtered = sessions.filter((session) => {
    const matchSearch =
      session.scenario.toLowerCase().includes(normalizedSearch) ||
      session.date.toLowerCase().includes(normalizedSearch);
    const matchScenario = scenario === 'All' || session.scenario === scenario;
    return matchSearch && matchScenario;
  });

  const totalPages = Math.ceil(filtered.length / ITEMS_PER_PAGE);
  const currentPage = totalPages === 0 ? 1 : Math.min(page, totalPages);
  const paginated = filtered.slice(
    (currentPage - 1) * ITEMS_PER_PAGE,
    currentPage * ITEMS_PER_PAGE,
  );
  const visiblePages = getVisiblePages(currentPage, totalPages);

  useEffect(() => {
    if (page !== currentPage) setPage(currentPage);
  }, [currentPage, page]);

  return (
    <>
      <div
        className="mb-4 flex flex-wrap items-center gap-3"
        aria-label="Session filters"
      >
        <div className="relative min-w-[200px] flex-1 sm:max-w-sm">
          <Search
            aria-hidden="true"
            className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted"
          />
          <label htmlFor="session-search" className="sr-only">
            Search sessions
          </label>
          <input
            id="session-search"
            type="search"
            placeholder="Search sessions by keyword..."
            value={search}
            onChange={(event) => {
              setSearch(event.target.value);
              setPage(1);
            }}
            className={`${styles.inputBase} ${styles.inputWithIcon}`}
          />
        </div>
        <label htmlFor="scenario-filter" className="sr-only">
          Filter by scenario
        </label>
        <select
          id="scenario-filter"
          value={scenario}
          onChange={(event) => {
            setScenario(event.target.value);
            setPage(1);
          }}
          className={`${styles.selectBase} w-full sm:w-auto`}
        >
          <option value="All">Scenario: All</option>
          {scenarios.map((value) => (
            <option key={value} value={value}>
              {value}
            </option>
          ))}
        </select>
      </div>

      <div className={`${styles.tableContainer} mb-6`} aria-label="Sessions">
        <div
          className={`hidden grid-cols-12 px-6 py-3 md:grid ${styles.tableHeaderGroup}`}
          aria-hidden="true"
        >
          <div className="col-span-3">Date &amp; Time</div>
          <div className="col-span-3">Scenario Type</div>
          <div className="col-span-4">AI Performance Score</div>
          <div className="col-span-2 text-right">Actions</div>
        </div>

        {paginated.map((session) => (
          <SessionRow
            key={session.id}
            session={session}
            actionLabel={actionLabel}
            onClick={() => onRowClick(session.id)}
            onRefresh={onRefresh}
          />
        ))}
      </div>

      {totalPages > 0 && (
        <nav
          className="mb-8 flex flex-col items-center justify-between gap-4 sm:flex-row"
          aria-label="Session pages"
        >
          <p className="text-sm text-muted" aria-live="polite">
            Showing{' '}
            <span className="font-bold text-white">
              {(currentPage - 1) * ITEMS_PER_PAGE + 1}
            </span>{' '}
            to{' '}
            <span className="font-bold text-white">
              {Math.min(currentPage * ITEMS_PER_PAGE, filtered.length)}
            </span>{' '}
            of <span className="font-bold text-white">{filtered.length}</span>{' '}
            sessions
          </p>
          <div className="flex items-center gap-2">
            <PageButton
              label="Previous page"
              disabled={currentPage === 1}
              onClick={() => setPage(Math.max(1, currentPage - 1))}
            >
              <ChevronLeft aria-hidden="true" className="h-4 w-4" />
            </PageButton>
            {visiblePages.map((pageNumber) => (
              <button
                key={pageNumber}
                type="button"
                aria-label={`Page ${pageNumber}`}
                aria-current={currentPage === pageNumber ? 'page' : undefined}
                onClick={() => setPage(pageNumber)}
                className={`h-9 w-9 rounded-lg text-sm font-bold transition-colors ${
                  currentPage === pageNumber
                    ? 'bg-brand text-brand-contrast'
                    : 'border border-border-subtle bg-surface text-secondary hover:border-brand'
                }`}
              >
                {pageNumber}
              </button>
            ))}
            <PageButton
              label="Next page"
              disabled={currentPage === totalPages}
              onClick={() => setPage(Math.min(totalPages, currentPage + 1))}
            >
              <ChevronRight aria-hidden="true" className="h-4 w-4" />
            </PageButton>
          </div>
        </nav>
      )}
    </>
  );
}

function PageButton({
  children,
  disabled,
  label,
  onClick,
}: {
  children: React.ReactNode;
  disabled: boolean;
  label: string;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      aria-label={label}
      onClick={onClick}
      disabled={disabled}
      className="flex h-9 w-9 items-center justify-center rounded-lg border border-border-subtle bg-surface text-secondary transition-colors hover:border-brand disabled:cursor-not-allowed disabled:opacity-40"
    >
      {children}
    </button>
  );
}

function SessionRow({
  session,
  actionLabel,
  onClick,
  onRefresh,
}: {
  session: SessionListItem;
  actionLabel: string;
  onClick: () => void;
  onRefresh?: () => void;
}) {
  const { status } = useSessionPolling(
    session.id,
    session.backendStatus,
    onRefresh,
  );
  const canOpenReport =
    status === 'Completed' ||
    status === 'Processing Analysis' ||
    status === 'Failed';

  return (
    <button
      type="button"
      onClick={onClick}
      disabled={!canOpenReport}
      aria-label={`${actionLabel}: ${session.scenario} session from ${session.date} at ${session.time}`}
      className="grid w-full grid-cols-1 gap-4 border-b border-[#1a1c25] px-4 py-5 text-left transition-colors last:border-0 enabled:hover:bg-white/5 disabled:cursor-not-allowed disabled:opacity-60 md:grid-cols-12 md:gap-0 md:px-6"
    >
      <div className="grid grid-cols-[7rem_1fr] items-center md:col-span-3 md:block">
        <span className="text-xs font-bold uppercase tracking-wider text-muted md:hidden">
          Date
        </span>
        <div>
          <p className="text-sm font-semibold text-white">{session.date}</p>
          <p className={styles.textMuted}>{session.time}</p>
        </div>
      </div>

      <div className="grid grid-cols-[7rem_1fr] items-center md:col-span-3 md:flex">
        <span className="text-xs font-bold uppercase tracking-wider text-muted md:hidden">
          Scenario
        </span>
        <ScenarioBadge scenario={session.scenario} />
      </div>

      <div className="grid grid-cols-[7rem_1fr] items-center md:col-span-4 md:flex md:gap-3">
        <span className="text-xs font-bold uppercase tracking-wider text-muted md:hidden">
          Performance
        </span>
        {status === 'Completed' && session.score != null ? (
          <ScoreProgressBar score={session.score} />
        ) : (
          <StatusBadge status={status} />
        )}
      </div>

      <div className="grid grid-cols-[7rem_1fr] items-center md:col-span-2 md:flex md:justify-end">
        <span className="text-xs font-bold uppercase tracking-wider text-muted md:hidden">
          Action
        </span>
        <span
          className={
            canOpenReport
              ? 'text-sm font-bold text-brand-soft'
              : 'text-xs font-bold text-muted'
          }
        >
          {canOpenReport ? actionLabel : 'Waiting...'}
        </span>
      </div>
    </button>
  );
}
