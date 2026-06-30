import type { ReactNode } from 'react';

function SkeletonBlock({ className }: { className: string }) {
  return (
    <div
      aria-hidden="true"
      className={`animate-pulse rounded-full bg-[#2a3325] ${className}`}
    />
  );
}

function SkeletonCard({ children }: { children: ReactNode }) {
  return (
    <div className="rounded-3xl border border-[#2a3325] bg-[#121610]/70 p-6">
      {children}
    </div>
  );
}

export function DashboardSkeleton() {
  return (
    <section
      role="status"
      aria-live="polite"
      aria-label="Loading dashboard"
      className="space-y-6"
    >
      <span className="sr-only">Loading dashboard...</span>
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {Array.from({ length: 4 }, (_, index) => (
          <SkeletonCard key={index}>
            <div className="flex items-start justify-between gap-4">
              <div className="space-y-4">
                <SkeletonBlock className="h-4 w-24" />
                <SkeletonBlock className="h-8 w-20" />
                <SkeletonBlock className="h-3 w-32" />
              </div>
              <SkeletonBlock className="h-12 w-12 rounded-2xl" />
            </div>
          </SkeletonCard>
        ))}
      </div>
      <div className="grid gap-4 xl:grid-cols-[1.4fr_1fr]">
        <SkeletonCard>
          <SkeletonBlock className="mb-8 h-5 w-48" />
          <div className="flex h-64 items-end gap-3">
            {[44, 70, 52, 86, 62, 74, 55].map((height, index) => (
              <div
                key={index}
                aria-hidden="true"
                className="flex-1 animate-pulse rounded-t-2xl bg-[#2a3325]"
                style={{ height: `${height}%` }}
              />
            ))}
          </div>
        </SkeletonCard>
        <SkeletonCard>
          <SkeletonBlock className="mb-8 h-5 w-40" />
          <div className="space-y-5">
            {Array.from({ length: 4 }, (_, index) => (
              <div key={index} className="flex items-center gap-4">
                <SkeletonBlock className="h-12 w-12 rounded-2xl" />
                <div className="flex-1 space-y-3">
                  <SkeletonBlock className="h-4 w-2/3" />
                  <SkeletonBlock className="h-3 w-1/2" />
                </div>
              </div>
            ))}
          </div>
        </SkeletonCard>
      </div>
    </section>
  );
}

export function LibrarySkeleton() {
  return (
    <section
      role="status"
      aria-live="polite"
      aria-label="Loading library files"
      className="space-y-8"
    >
      <span className="sr-only">Loading library files...</span>
      <div className="rounded-3xl border-2 border-dashed border-[#46513c] bg-[#121610]/70 px-6 py-16">
        <div className="mx-auto flex max-w-md flex-col items-center gap-4 text-center">
          <SkeletonBlock className="h-16 w-16 rounded-full" />
          <SkeletonBlock className="h-5 w-56" />
          <SkeletonBlock className="h-4 w-72 max-w-full" />
          <SkeletonBlock className="h-12 w-36 rounded-2xl" />
        </div>
      </div>

      <div className="flex flex-wrap items-center justify-between gap-4">
        <SkeletonBlock className="h-7 w-36" />
        <SkeletonBlock className="h-11 w-full max-w-xs rounded-2xl" />
      </div>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
        {Array.from({ length: 3 }, (_, index) => (
          <SkeletonCard key={index}>
            <div className="flex items-start gap-4">
              <SkeletonBlock className="h-14 w-14 rounded-2xl" />
              <div className="flex-1 space-y-3">
                <SkeletonBlock className="h-5 w-3/4" />
                <div className="flex gap-2">
                  <SkeletonBlock className="h-6 w-14 rounded-lg" />
                  <SkeletonBlock className="h-5 w-24" />
                </div>
                <SkeletonBlock className="h-4 w-32" />
              </div>
            </div>
          </SkeletonCard>
        ))}
      </div>
    </section>
  );
}

export function SessionListSkeleton() {
  return (
    <section
      role="status"
      aria-live="polite"
      aria-label="Loading sessions"
      className="space-y-4"
    >
      <span className="sr-only">Loading sessions...</span>
      <div className="flex items-center justify-between gap-4">
        <SkeletonBlock className="h-5 w-36" />
        <SkeletonBlock className="h-10 w-full max-w-xs rounded-2xl" />
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        {Array.from({ length: 4 }, (_, index) => (
          <SkeletonCard key={index}>
            <div className="mb-5 flex items-start gap-4">
              <SkeletonBlock className="h-14 w-14 rounded-2xl" />
              <div className="flex-1 space-y-3">
                <SkeletonBlock className="h-5 w-2/3" />
                <div className="flex gap-2">
                  <SkeletonBlock className="h-6 w-14 rounded-lg" />
                  <SkeletonBlock className="h-5 w-24" />
                  <SkeletonBlock className="h-5 w-28" />
                </div>
              </div>
            </div>
            <SkeletonBlock className="h-4 w-40" />
          </SkeletonCard>
        ))}
      </div>
    </section>
  );
}

export function UserManagementSkeleton() {
  return (
    <section
      role="status"
      aria-live="polite"
      aria-label="Loading admin users"
      className="rounded-3xl border border-[#2a3325] bg-[#121610]/70 p-6"
    >
      <span className="sr-only">Loading admin users...</span>
      <div className="mb-6 flex flex-wrap items-center justify-between gap-4">
        <SkeletonBlock className="h-6 w-28" />
        <SkeletonBlock className="h-11 w-full max-w-xs rounded-2xl" />
      </div>
      <div className="space-y-4">
        {Array.from({ length: 5 }, (_, index) => (
          <div
            key={index}
            className="grid gap-4 rounded-2xl border border-[#2a3325] p-4 md:grid-cols-[1.5fr_0.6fr_0.8fr_0.5fr]"
          >
            <div className="flex items-center gap-3">
              <SkeletonBlock className="h-11 w-11 rounded-full" />
              <div className="flex-1 space-y-2">
                <SkeletonBlock className="h-4 w-36" />
                <SkeletonBlock className="h-3 w-48" />
              </div>
            </div>
            <SkeletonBlock className="h-4 w-16" />
            <SkeletonBlock className="h-4 w-28" />
            <SkeletonBlock className="h-8 w-20 rounded-xl" />
          </div>
        ))}
      </div>
    </section>
  );
}

export function SessionAnalyticsSkeleton() {
  return (
    <section
      role="status"
      aria-live="polite"
      aria-label="Loading session analytics"
      className="space-y-6"
    >
      <span className="sr-only">Loading session analytics...</span>
      <SkeletonBlock className="h-5 w-32" />

      <div className="space-y-3">
        <SkeletonBlock className="h-10 w-80 max-w-full" />
        <SkeletonBlock className="h-5 w-[32rem] max-w-full" />
      </div>

      <div className="flex gap-3">
        <SkeletonBlock className="h-8 w-24 rounded-xl" />
        <SkeletonBlock className="h-8 w-36 rounded-xl" />
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        {Array.from({ length: 3 }, (_, index) => (
          <SkeletonCard key={index}>
            <SkeletonBlock className="mb-5 h-4 w-28" />
            <SkeletonBlock className="mb-4 h-9 w-20" />
            <SkeletonBlock className="h-3 w-full" />
          </SkeletonCard>
        ))}
      </div>

      <SkeletonCard>
        <div className="flex items-start gap-4">
          <SkeletonBlock className="h-12 w-12 rounded-2xl" />
          <div className="flex-1 space-y-3">
            <SkeletonBlock className="h-4 w-40" />
            <SkeletonBlock className="h-6 w-full" />
            <SkeletonBlock className="h-6 w-4/5" />
          </div>
        </div>
      </SkeletonCard>

      <div className="grid grid-cols-1 gap-5 lg:grid-cols-3">
        {Array.from({ length: 3 }, (_, index) => (
          <SkeletonCard key={index}>
            <SkeletonBlock className="mb-6 h-6 w-44" />
            <div className="space-y-4">
              {Array.from({ length: 3 }, (_, itemIndex) => (
                <div key={itemIndex} className="space-y-2">
                  <SkeletonBlock className="h-4 w-2/3" />
                  <SkeletonBlock className="h-3 w-full" />
                  <SkeletonBlock className="h-3 w-4/5" />
                </div>
              ))}
            </div>
          </SkeletonCard>
        ))}
      </div>
    </section>
  );
}
