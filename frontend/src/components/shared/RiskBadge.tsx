interface RiskBadgeProps {
  category: 'green' | 'yellow' | 'red' | string;
  size?: 'sm' | 'md' | 'lg';
}

const colorMap: Record<string, string> = {
  green: 'bg-[#22c55e]/15 text-[#22c55e] border-[#22c55e]/30',
  yellow: 'bg-[#eab308]/15 text-[#eab308] border-[#eab308]/30',
  red: 'bg-[#ef4444]/15 text-[#ef4444] border-[#ef4444]/30',
};

const labelMap: Record<string, string> = {
  green: 'Low Risk',
  yellow: 'Medium Risk',
  red: 'High Risk',
};

const sizeMap = {
  sm: 'text-[10px] px-2 py-0.5',
  md: 'text-xs px-3 py-1',
  lg: 'text-sm px-4 py-1.5',
};

export default function RiskBadge({ category, size = 'md' }: RiskBadgeProps) {
  return (
    <span className={`inline-flex items-center rounded-full border font-medium ${colorMap[category] || colorMap.yellow} ${sizeMap[size]}`}>
      {labelMap[category] || category}
    </span>
  );
}
