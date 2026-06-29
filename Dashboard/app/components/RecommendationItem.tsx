// app/components/RecommendationItem.tsx

interface RecommendationItemProps {
  num: number;
  title: string;
  desc: string;
}

export function RecommendationItem({ num, title, desc }: RecommendationItemProps) {
  return (
    <div className="flex gap-4">
      <div className="w-8 h-8 rounded-full bg-[#5c7cff] text-white flex items-center justify-center font-black text-xs flex-shrink-0">
        {num}
      </div>
      <div>
        <h4 className="text-white font-bold text-sm mb-1">{title}</h4>
        <p className="text-[#5c6484] text-sm leading-relaxed">{desc}</p>
      </div>
    </div>
  );
}
