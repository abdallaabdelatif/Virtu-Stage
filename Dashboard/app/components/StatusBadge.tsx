export function StatusBadge({ status }: { status: string }) {
  if (status === 'Completed') {
    return (
      <span className="px-2 py-1 rounded-lg text-xs font-bold bg-[#0bda62]/10 text-[#0bda62]">
        Completed
      </span>
    );
  }
  if (status === 'In Progress') {
    return (
      <span className="px-2 py-1 rounded-lg text-xs font-bold bg-[#5c7cff]/10 text-[#5c7cff]">
        In Progress
      </span>
    );
  }
  if (status === 'Processing Analysis' || status === 'Pending') {
    return (
      <span className="px-2 py-1 rounded-lg text-xs font-bold bg-[#FFB703]/10 text-[#FFB703]">
        {status}
        <span className="ml-2 animate-pulse">...</span>
      </span>
    );
  }
  return (
    <span className="px-2 py-1 rounded-lg text-xs font-bold bg-red-500/10 text-red-400">
      {status}
    </span>
  );
}
