import type { CreditOption } from '../../types';
import OptionCard from './OptionCard';

interface OptionsPanelProps {
  options: CreditOption[];
  maxEL: number;
  onSelect?: (option: CreditOption) => void;
}

export default function OptionsPanel({ options, maxEL, onSelect }: OptionsPanelProps) {
  if (!options || options.length === 0) return null;

  return (
    <div>
      <h3 className="text-sm font-semibold text-[#8888bb] uppercase tracking-wider mb-4">
        Credit Term Options
      </h3>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {options.map((opt, i) => (
          <OptionCard
            key={opt.option_id}
            option={opt}
            index={i}
            maxEL={maxEL}
            onSelect={onSelect}
          />
        ))}
      </div>
    </div>
  );
}
