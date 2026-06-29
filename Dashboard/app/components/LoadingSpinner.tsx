import { Loader2 } from "lucide-react"

export function LoadingSpinner({ text = "Loading..." }: { text?: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-20 min-h-[50vh]">
      <Loader2 className="w-10 h-10 text-[#5c7cff] animate-spin mb-4" />
      <p className="text-[#9aa1bc] font-bold">{text}</p>
    </div>
  )
}
