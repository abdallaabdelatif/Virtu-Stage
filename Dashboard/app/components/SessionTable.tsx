import { useState } from 'react';
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

export function SessionTable({
  sessions,
  actionLabel,
  onRowClick,
  onRefresh,
}: SessionTableProps) {
  const [search, setSearch] = useState('');
  const [scenario, setScenario] = useState('All');
  const [page, setPage] = useState(1);

  const filtered = sessions.filter((s) => {
    const matchSearch =
      s.scenario.toLowerCase().includes(search.toLowerCase()) ||
      s.date.toLowerCase().includes(search.toLowerCase());
    const matchScenario = scenario === 'All' || s.scenario === scenario;
    return matchSearch && matchScenario;
  });

  const totalPages = Math.ceil(filtered.length / ITEMS_PER_PAGE);
  const paginated = filtered.slice(
    (page - 1) * ITEMS_PER_PAGE,
    page * ITEMS_PER_PAGE,
  );

  return (
    <>
      <div className="flex flex-wrap items-center gap-3 mb-4">
        <div className="relative flex-1 min-w-[200px] max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#5c6484]" />
          <input
            type="text"
            placeholder="Search sessions by keyword..."
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              setPage(1);
            }}
            className={`${styles.inputBase} ${styles.inputWithIcon}`}
          />
        </div>
        <select
          value={scenario}
          onChange={(e) => {
            setScenario(e.target.value);
            setPage(1);
          }}
          className={styles.selectBase}
        >
          <option value="All">Scenario: All</option>
          <option>Job Interview</option>
          <option>Public Speaking</option>
        </select>
      </div>

      <div className={`${styles.tableContainer} mb-6`}>
        <div
          className={`grid grid-cols-12 px-6 py-3 ${styles.tableHeaderGroup}`}
        >
          <div className="col-span-3">Date & Time</div>
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
        <div className={`${styles.flexBetween} mb-8`}>
          <p className="text-[#5c6484] text-sm">
            Showing{' '}
            <span className="text-white font-bold">
              {Math.min((page - 1) * ITEMS_PER_PAGE + 1, filtered.length)}
            </span>{' '}
            to{' '}
            <span className="text-white font-bold">
              {Math.min(page * ITEMS_PER_PAGE, filtered.length)}
            </span>{' '}
            of <span className="text-white font-bold">{filtered.length}</span>{' '}
            sessions
          </p>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setPage(Math.max(1, page - 1))}
              disabled={page === 1}
              className="w-9 h-9 rounded-lg bg-[#12141c] border border-[#272b3a] flex items-center justify-center text-[#9aa1bc] hover:border-[#5c7cff] disabled:opacity-40 transition-colors"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            {Array.from({ length: totalPages }, (_, i) => i + 1).map((p) => (
              <button
                key={p}
                onClick={() => setPage(p)}
                className={`w-9 h-9 rounded-lg text-sm font-bold transition-colors ${
                  page === p
                    ? 'bg-[#5c7cff] text-white'
                    : 'bg-[#12141c] border border-[#272b3a] text-[#9aa1bc] hover:border-[#5c7cff]'
                }`}
              >
                {p}
              </button>
            ))}
            <button
              onClick={() => setPage(Math.min(totalPages, page + 1))}
              disabled={page === totalPages || totalPages === 0}
              className="w-9 h-9 rounded-lg bg-[#12141c] border border-[#272b3a] flex items-center justify-center text-[#9aa1bc] hover:border-[#5c7cff] disabled:opacity-40 transition-colors"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}
    </>
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
  const isActive = session.backendStatus !== 'completed';
  const { status } = useSessionPolling(
    session.id,
    session.backendStatus,
    onRefresh,
  );

  const currentStatus = isActive ? status : session.status;
  const canOpenReport =
    currentStatus === 'Completed' ||
    currentStatus === 'Processing Analysis' ||
    currentStatus === 'Failed';

  return (
    <div
      onClick={() => canOpenReport && onClick()}
      className={`grid grid-cols-12 px-6 py-5 transition-colors last:border-0 border-b border-[#1a1c25] ${
        !canOpenReport
          ? 'opacity-60 cursor-not-allowed'
          : 'hover:bg-white/5 cursor-pointer'
      }`}
    >
      <div className="col-span-3">
        <p className="text-white font-semibold text-sm">{session.date}</p>
        <p className={styles.textMuted}>{session.time}</p>
      </div>

      <div className="col-span-3 flex items-center">
        <ScenarioBadge scenario={session.scenario} />
      </div>

      <div className="col-span-4 flex items-center gap-3">
        {currentStatus === 'Completed' && session.score != null ? (
          <ScoreProgressBar score={session.score} />
        ) : (
          <StatusBadge status={currentStatus} />
        )}
      </div>

      <div
        className="col-span-2 flex items-center justify-end gap-2"
        onClick={(e) => {
          if (!canOpenReport) e.stopPropagation();
        }}
      >
        {!canOpenReport ? (
          <span className="text-[#5c6484] text-xs font-bold">Waiting...</span>
        ) : (
          <button
            onClick={(e) => {
              e.stopPropagation();
              onClick();
            }}
            className={styles.btnLink}
          >
            {actionLabel}
          </button>
        )}
      </div>
    </div>
  );
}
