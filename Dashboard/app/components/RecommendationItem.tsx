// app/components/RecommendationItem.tsx

interface RecommendationItemProps {
  num: number;
  title: string;
  desc: string;
}

export function RecommendationItem({
  num,
  title,
  desc,
}: RecommendationItemProps) {
  return (
    <div className="flex gap-4">
      <div className="w-9 h-9 rounded-full bg-brand text-brand-contrast flex items-center justify-center font-black text-sm flex-shrink-0">
        {num}
      </div>
      <div>
        <h4 className="text-white font-bold text-base mb-1">{title}</h4>
        <p className="text-[#b8c0b0] text-sm leading-relaxed sm:text-base">
          {desc}
        </p>
      </div>
    </div>
  );
}
