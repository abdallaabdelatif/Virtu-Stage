import { helpers } from "../utils/styles"
import { Star } from "lucide-react"

export function ScoreBadge({ score, className = "", showIcon = true }: { score: number, className?: string, showIcon?: boolean }) {
  return (
    <span className={`font-black flex items-center gap-1 ${helpers.scoreColor(score)} ${className}`}>
      {showIcon && <Star className={`w-4 h-4 ${score >= 60 ? "text-[#FFB703]" : "text-red-400"}`} />}
      {score}/100
    </span>
  )
}

export function ScoreProgressBar({ score }: { score: number }) {
  return (
    <div className="flex items-center gap-3 w-full">
      <div className="flex-1 h-2 bg-[#272b3a] rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-1000 ${helpers.scoreBg(score)}`}
          style={{ width: `${score}%` }}
        />
      </div>
      <span className={`font-black text-sm w-12 text-right transition-colors duration-1000 ${helpers.scoreColor(score)}`}>
        {score}%
      </span>
    </div>
  )
}
