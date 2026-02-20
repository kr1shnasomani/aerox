import { motion } from 'framer-motion';
import { Zap, Calendar, Wallet } from 'lucide-react';
import type { CreditOption } from '../../types';

interface OptionCardProps {
  option: CreditOption;
  index: number;
  maxEL: number;
  onSelect?: (option: CreditOption) => void;
}

const accents = [
  { bg: 'from-[#22c55e]/10 to-transparent', border: 'border-[#22c55e]/20', text: 'text-[#22c55e]', icon: Zap, label: 'Recommended' },
  { bg: 'from-[#eab308]/10 to-transparent', border: 'border-[#eab308]/20', text: 'text-[#eab308]', icon: Calendar, label: 'Standard' },
  { bg: 'from-[#ef4444]/10 to-transparent', border: 'border-[#ef4444]/20', text: 'text-[#ef4444]', icon: Wallet, label: 'Conservative' },
];

export default function OptionCard({ option, index, maxEL, onSelect }: OptionCardProps) {
  const accent = accents[index] || accents[2];
  const Icon = accent.icon;
  const elPercent = Math.min((option.expected_loss / maxEL) * 100, 100);

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.15 }}
      className={`relative rounded-xl border ${accent.border} bg-gradient-to-b ${accent.bg} p-5 hover:bg-white/[0.03] transition-all cursor-pointer`}
      onClick={() => onSelect?.(option)}
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${accent.text} bg-white/5`}>
            <Icon size={16} />
          </div>
          <div>
            <h4 className="text-sm font-bold text-white">Option {option.option_id}</h4>
            <p className="text-[10px] text-[#666]">{accent.label}</p>
          </div>
        </div>
        {index === 0 && (
          <span className="text-[10px] px-2 py-1 rounded-full bg-[#22c55e]/15 text-[#22c55e] border border-[#22c55e]/20">
            Lowest Friction
          </span>
        )}
      </div>

      {/* Details */}
      <div className="space-y-2 text-sm">
        <div className="flex justify-between">
          <span className="text-[#8888bb]">Settlement</span>
          <span className="font-mono text-white">{option.settlement_days} days</span>
        </div>
        <div className="flex justify-between">
          <span className="text-[#8888bb]">Upfront</span>
          <span className="font-mono text-white">₹{option.upfront_amount.toLocaleString()}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-[#8888bb]">Approved</span>
          <span className="font-mono text-white">₹{option.approved_amount.toLocaleString()}</span>
        </div>
      </div>

      {/* EL Bar */}
      <div className="mt-4 pt-4 border-t border-white/5">
        <div className="flex justify-between text-xs mb-1">
          <span className="text-[#8888bb]">Expected Loss</span>
          <span className={`font-mono font-bold ${accent.text}`}>₹{option.expected_loss.toLocaleString()}</span>
        </div>
        <div className="h-2 bg-white/5 rounded-full overflow-hidden">
          <motion.div
            initial={{ width: 0 }}
            animate={{ width: `${elPercent}%` }}
            transition={{ delay: 0.5 + index * 0.15, duration: 0.8 }}
            className={`h-full rounded-full ${
              elPercent < 40 ? 'bg-[#22c55e]' : elPercent < 70 ? 'bg-[#eab308]' : 'bg-[#ef4444]'
            }`}
          />
        </div>
        <p className="text-[10px] text-[#555] mt-1">
          {elPercent.toFixed(0)}% of ₹{maxEL.toLocaleString()} limit
        </p>
      </div>

      {/* Friction */}
      <div className="mt-3 flex items-center gap-2">
        <span className="text-[10px] text-[#666]">Friction</span>
        <div className="flex-1 h-1.5 bg-white/5 rounded-full overflow-hidden">
          <div
            className="h-full rounded-full bg-[#8b5cf6]"
            style={{ width: `${(option.friction_score / 10) * 100}%` }}
          />
        </div>
        <span className="text-[10px] font-mono text-[#8888bb]">{option.friction_score}/10</span>
      </div>
    </motion.div>
  );
}
