export const styles = {
  // Container & Card Styles
  card: 'bg-[#1a2117] border border-[#46513c] rounded-2xl p-6',
  cardSub: 'bg-[#2a3325] rounded-2xl p-5',
  cardActive:
    'bg-[#1a2117] border border-brand shadow-xl shadow-brand/10 rounded-2xl p-6 relative overflow-hidden',
  cardInteractive:
    'bg-[#121610] border border-[#2a3325] hover:border-[#46513c] rounded-2xl p-5 transition-all hover:bg-white/5',

  // Text Styles
  pageTitle: 'text-3xl sm:text-4xl font-black tracking-tight text-white mb-1',
  pageSubtitle: 'text-secondary text-base',

  cardTitle: 'text-white font-black text-lg',
  cardSubtitle: 'text-secondary text-sm',

  heading2: 'text-white text-2xl font-black flex items-center gap-2 mb-4',
  heading3: 'text-white text-lg font-bold mb-3 flex items-center gap-2',

  labelMuted: 'text-muted text-xs font-bold uppercase tracking-wider',
  textMuted: 'text-muted text-xs',

  statValueLarge: 'text-white text-4xl sm:text-5xl font-black',

  // Forms & Inputs
  inputBase:
    'w-full bg-[#121610] border border-[#46513c] rounded-xl px-4 py-2.5 text-sm text-white placeholder:text-[#aeb4a8] focus:outline-none focus:border-brand transition-colors',
  inputWithIcon: 'pl-9',
  selectBase:
    'bg-[#121610] border border-[#46513c] rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-brand transition-colors',

  // Tables
  tableContainer:
    'bg-[#121610] border border-[#2a3325] rounded-2xl overflow-hidden',
  tableHeaderGroup:
    'text-[#aeb4a8] text-xs font-bold uppercase tracking-wider border-b border-[#2a3325]',
  tableRow:
    'border-b border-[#25301f] hover:bg-white/5 transition-colors last:border-0',

  // Flex Utilities
  flexCenter: 'flex items-center justify-center',
  flexBetween: 'flex items-center justify-between',
  flexStart: 'flex items-center justify-start',

  // Buttons
  btnPrimaryIcon:
    'flex items-center gap-2 bg-brand hover:bg-brand-hover text-brand-contrast text-sm font-bold px-5 h-11 rounded-xl transition-all shadow-lg shadow-brand/20',
  btnSecondaryIcon:
    'flex items-center gap-2 bg-[#2a3325] hover:bg-[#46513c] text-white text-sm font-bold h-12 px-5 rounded-xl transition-all',
  btnWhiteIcon:
    'flex items-center gap-2 bg-white hover:bg-gray-100 text-[#10130f] text-sm font-bold h-12 px-5 rounded-xl transition-all',
  btnLink: 'text-brand-soft text-sm font-bold hover:underline',
};

export const helpers = {
  scoreColor: (score: number) => {
    if (score >= 80) return 'text-[#0bda62]';
    if (score >= 60) return 'text-[#FFB703]';
    return 'text-red-400';
  },
  scoreBg: (score: number) => {
    if (score >= 80) return 'bg-[#0bda62]';
    if (score >= 60) return 'bg-[#FFB703]';
    return 'bg-red-400';
  },
};
