export const styles = {
  // Container & Card Styles
  card: "bg-[#1b1d28] border border-[#393f56] rounded-2xl p-6",
  cardSub: "bg-[#272b3a] rounded-2xl p-5",
  cardActive: "bg-[#1b1d28] border border-[#5c7cff] shadow-xl shadow-[#5c7cff]/10 rounded-2xl p-6 relative overflow-hidden",
  cardInteractive: "bg-[#12141c] border border-[#272b3a] hover:border-[#393f56] rounded-2xl p-5 transition-all hover:bg-white/5",
  
  // Text Styles
  pageTitle: "text-3xl sm:text-4xl font-black tracking-tight text-white mb-1",
  pageSubtitle: "text-[#9aa1bc] text-base",
  
  cardTitle: "text-white font-black text-lg",
  cardSubtitle: "text-[#9aa1bc] text-sm",
  
  heading2: "text-white text-2xl font-black flex items-center gap-2 mb-4",
  heading3: "text-white text-lg font-bold mb-3 flex items-center gap-2",

  labelMuted: "text-[#5c6484] text-xs font-bold uppercase tracking-wider",
  textMuted: "text-[#5c6484] text-xs",
  
  statValueLarge: "text-white text-4xl sm:text-5xl font-black",
  
  // Forms & Inputs
  inputBase: "w-full bg-[#12141c] border border-[#393f56] rounded-xl px-4 py-2.5 text-sm text-white placeholder:text-[#5c6484] focus:outline-none focus:border-[#5c7cff] transition-colors",
  inputWithIcon: "pl-9",
  selectBase: "bg-[#12141c] border border-[#393f56] rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-[#5c7cff] transition-colors",
  
  // Tables
  tableContainer: "bg-[#12141c] border border-[#272b3a] rounded-2xl overflow-hidden",
  tableHeaderGroup: "text-[#5c6484] text-xs font-bold uppercase tracking-wider border-b border-[#272b3a]",
  tableRow: "border-b border-[#1a1c25] hover:bg-white/5 transition-colors last:border-0",
  
  // Flex Utilities
  flexCenter: "flex items-center justify-center",
  flexBetween: "flex items-center justify-between",
  flexStart: "flex items-center justify-start",
  
  // Buttons
  btnPrimaryIcon: "flex items-center gap-2 bg-[#5c7cff] hover:bg-[#4a6aee] text-white text-sm font-bold px-5 h-11 rounded-xl transition-all shadow-lg shadow-[#5c7cff]/20",
  btnSecondaryIcon: "flex items-center gap-2 bg-[#272b3a] hover:bg-[#393f56] text-white text-sm font-bold h-12 px-5 rounded-xl transition-all",
  btnWhiteIcon: "flex items-center gap-2 bg-white hover:bg-gray-100 text-[#0f1323] text-sm font-bold h-12 px-5 rounded-xl transition-all",
  btnLink: "text-[#5c7cff] text-sm font-bold hover:underline",
}

export const helpers = {
  scoreColor: (score: number) => {
    if (score >= 80) return "text-[#0bda62]"
    if (score >= 60) return "text-[#FFB703]"
    return "text-red-400"
  },
  scoreBg: (score: number) => {
    if (score >= 80) return "bg-[#0bda62]"
    if (score >= 60) return "bg-[#FFB703]"
    return "bg-red-400"
  }
}
