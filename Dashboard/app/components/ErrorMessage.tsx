import { AlertCircle, RefreshCw } from "lucide-react"
import { Button } from "./Button"

interface ErrorMessageProps {
  title?: string
  message: string
  onRetry?: () => void
}

export function ErrorMessage({ title = "Something went wrong", message, onRetry }: ErrorMessageProps) {
  return (
    <div className="flex flex-col items-center justify-center py-20 min-h-[50vh] text-center">
      <div className="w-16 h-16 rounded-2xl bg-red-500/10 flex items-center justify-center mb-6">
        <AlertCircle className="w-8 h-8 text-red-400" />
      </div>
      <h3 className="text-white text-xl font-bold mb-2">{title}</h3>
      <p className="text-[#9aa1bc] max-w-md mb-8">{message}</p>
      
      {onRetry && (
        <Button onClick={onRetry} variant="secondary" className="gap-2">
          <RefreshCw className="w-4 h-4" />
          Try Again
        </Button>
      )}
    </div>
  )
}
