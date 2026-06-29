import type { LucideIcon } from 'lucide-react';

interface InputProps {
  label?: string
  type?: string
  placeholder?: string
  value: string
  onChange: (e: React.ChangeEvent<HTMLInputElement>) => void
  onKeyDown?: (e: React.KeyboardEvent<HTMLInputElement>) => void
  rightElement?: React.ReactNode
  extra?: React.ReactNode
  icon?: LucideIcon
  required?: boolean
  error?: boolean
}

export function Input({
  label,
  type = "text",
  placeholder,
  value,
  onChange,
  onKeyDown,
  rightElement,
  extra,
  icon: Icon,
  required = false,
  error = false,
}: InputProps) {
  return (
    <div className="flex flex-col gap-1.5 py-2">
      {(label || extra) && (
        <div className="flex justify-between items-center pb-1">
          {label && <p className="text-white text-sm font-medium">{label}</p>}
          {extra}
        </div>
      )}
      <div className="relative">
        <input
          type={type}
          placeholder={placeholder}
          value={value}
          onChange={onChange}
          onKeyDown={onKeyDown}
          required={required}
          aria-invalid={error}
          className={`w-full rounded-xl text-white border bg-[#12141c] focus:ring-2 focus:outline-none h-14 ${Icon ? 'px-11' : 'px-4'} pr-12 text-base placeholder:text-[#5c6484] transition-all ${
            error
              ? 'border-red-500 focus:border-red-400 focus:ring-red-500/30'
              : 'border-[#393f56] focus:border-[#5c7cff] focus:ring-[#5c7cff]/50'
          }`}
        />
        {Icon && (
          <div className="absolute left-4 top-1/2 -translate-y-1/2">
            <Icon className="w-5 h-5 text-[#5c6484]" />
          </div>
        )}
        {rightElement && (
          <div className="absolute right-4 top-1/2 -translate-y-1/2">
            {rightElement}
          </div>
        )}
      </div>
    </div>
  )
}
