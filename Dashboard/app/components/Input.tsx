import { useId, type InputHTMLAttributes, type ReactNode } from 'react';
import type { LucideIcon } from 'lucide-react';

interface InputProps extends Omit<
  InputHTMLAttributes<HTMLInputElement>,
  'value'
> {
  label?: string;
  value: string;
  rightElement?: ReactNode;
  extra?: ReactNode;
  icon?: LucideIcon;
  error?: boolean;
}

export function Input({
  label,
  type = 'text',
  placeholder,
  value,
  onChange,
  onKeyDown,
  rightElement,
  extra,
  icon: Icon,
  error = false,
  id,
  className = '',
  ...inputProps
}: InputProps) {
  const generatedId = useId();
  const inputId = id ?? generatedId;

  return (
    <div className="flex flex-col gap-1.5 py-2">
      {(label || extra) && (
        <div className="flex justify-between items-center pb-1">
          {label && (
            <label htmlFor={inputId} className="text-white text-sm font-medium">
              {label}
            </label>
          )}
          {extra}
        </div>
      )}
      <div className="relative">
        <input
          id={inputId}
          type={type}
          placeholder={placeholder}
          value={value}
          onChange={onChange}
          onKeyDown={onKeyDown}
          aria-invalid={error}
          className={`w-full rounded-xl text-white border bg-surface focus:ring-2 focus:outline-none h-14 ${Icon ? 'px-11' : 'px-4'} ${rightElement ? 'pr-12' : 'pr-4'} text-base placeholder:text-muted transition-all ${
            error
              ? 'border-red-500 focus:border-red-400 focus:ring-red-500/30'
              : 'border-border-strong focus:border-brand focus:ring-brand/50'
          } ${className}`}
          {...inputProps}
        />
        {Icon && (
          <div className="absolute left-4 top-1/2 -translate-y-1/2">
            <Icon aria-hidden="true" className="w-5 h-5 text-muted" />
          </div>
        )}
        {rightElement && (
          <div className="absolute right-4 top-1/2 -translate-y-1/2">
            {rightElement}
          </div>
        )}
      </div>
    </div>
  );
}
