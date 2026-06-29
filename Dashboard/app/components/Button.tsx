interface ButtonProps {
  children: React.ReactNode
  onClick?: () => void
  disabled?: boolean
  loading?: boolean
  variant?: "primary" | "secondary" | "danger" | "ghost"
  fullWidth?: boolean
  type?: "button" | "submit"
  size?: "sm" | "md" | "lg"
  className?: string
}

const variants = {
  primary: "bg-[#5c7cff] text-white hover:brightness-110 shadow-xl shadow-[#5c7cff]/20",
  secondary: "bg-[#272b3a] text-white hover:bg-[#393f56]",
  danger: "bg-red-500/10 text-red-400 border border-red-500/30 hover:bg-red-500/20",
  ghost: "bg-transparent border border-[#393f56] text-white hover:bg-white/5",
}

const sizes = {
  sm: "h-9 px-4 text-sm",
  md: "h-12 px-5 text-sm",
  lg: "h-14 px-6 text-base",
}

export function Button({
  children,
  onClick,
  disabled,
  loading,
  variant = "primary",
  fullWidth = false,
  type = "button",
  size = "lg",
  className = "",
}: ButtonProps) {
  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled || loading}
      className={`
        flex items-center justify-center rounded-xl font-bold
        active:scale-[0.98] transition-all
        disabled:opacity-60 disabled:cursor-not-allowed
        ${variants[variant]}
        ${sizes[size]}
        ${fullWidth ? "w-full" : ""}
        ${className}
      `}
    >
      {loading ? (
        <span className="flex items-center gap-2">
          <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24" fill="none">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
          </svg>
          Loading...
        </span>
      ) : children}
    </button>
  )
}
