import { motion } from 'framer-motion';
import { CheckCircle, XCircle, AlertTriangle } from 'lucide-react';
import type { ProcessingResult } from '../../types';

interface DecisionBannerProps {
  result: ProcessingResult;
}

const config = {
  APPROVED: {
    icon: CheckCircle,
    title: 'AUTO-APPROVED',
    subtitle: 'Low risk - standard terms applied',
    bg: 'from-[#22c55e]/20 to-[#22c55e]/5',
    border: 'border-[#22c55e]/30',
    text: 'text-[#22c55e]',
    glow: 'shadow-[0_0_60px_rgba(34,197,94,0.15)]',
  },
  NEGOTIATE: {
    icon: AlertTriangle,
    title: 'NEGOTIATION REQUIRED',
    subtitle: '3 credit term options generated',
    bg: 'from-[#eab308]/20 to-[#eab308]/5',
    border: 'border-[#eab308]/30',
    text: 'text-[#eab308]',
    glow: 'shadow-[0_0_60px_rgba(234,179,8,0.15)]',
  },
  BLOCKED: {
    icon: XCircle,
    title: 'BLOCKED',
    subtitle: 'High risk detected',
    bg: 'from-[#ef4444]/20 to-[#ef4444]/5',
    border: 'border-[#ef4444]/30',
    text: 'text-[#ef4444]',
    glow: 'shadow-[0_0_60px_rgba(239,68,68,0.15)]',
  },
};

export default function DecisionBanner({ result }: DecisionBannerProps) {
  const c = config[result.decision] || config.BLOCKED;
  const Icon = c.icon;

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.5, ease: 'easeOut' }}
      className={`relative overflow-hidden rounded-xl border ${c.border} ${c.glow} bg-gradient-to-r ${c.bg} p-6`}
    >
      <div className="flex items-center gap-4">
        <motion.div
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ delay: 0.2, type: 'spring', stiffness: 200 }}
        >
          <Icon size={48} className={c.text} />
        </motion.div>
        <div>
          <h2 className={`text-2xl font-bold ${c.text}`}>{c.title}</h2>
          <p className="text-sm text-[#8888bb] mt-1">{c.subtitle}</p>
          {result.decision === 'APPROVED' && result.approved_amount && (
            <p className="text-sm text-[#e2e2ff] mt-2">
              Approved <span className="font-semibold text-[#22c55e]">₹{result.approved_amount.toLocaleString()}</span> with {result.settlement_days}-day settlement
            </p>
          )}
          {result.decision === 'BLOCKED' && result.reason && (
            <p className="text-sm text-[#e2e2ff] mt-2">
              Reason: <span className="font-mono text-[#ef4444]">{result.reason}</span>
            </p>
          )}
          {result.decision === 'NEGOTIATE' && result.options && (
            <p className="text-sm text-[#e2e2ff] mt-2">
              <span className="font-semibold text-[#eab308]">{result.options.length} options</span> ready for agency selection
            </p>
          )}
        </div>
      </div>

      {/* Scores summary */}
      <div className="flex gap-6 mt-4 pt-4 border-t border-white/5">
        <div>
          <span className="text-[10px] text-[#666] uppercase">Intent</span>
          <p className={`text-lg font-mono font-bold ${
            result.ml_scores.intent_score >= 0.6 ? 'text-[#ef4444]' :
            result.ml_scores.intent_score >= 0.4 ? 'text-[#eab308]' : 'text-[#22c55e]'
          }`}>
            {result.ml_scores.intent_score.toFixed(3)}
          </p>
        </div>
        <div>
          <span className="text-[10px] text-[#666] uppercase">Capacity</span>
          <p className={`text-lg font-mono font-bold ${
            result.ml_scores.capacity_score >= 0.7 ? 'text-[#22c55e]' :
            result.ml_scores.capacity_score >= 0.4 ? 'text-[#eab308]' : 'text-[#ef4444]'
          }`}>
            {result.ml_scores.capacity_score.toFixed(3)}
          </p>
        </div>
        <div>
          <span className="text-[10px] text-[#666] uppercase">PD (30d)</span>
          <p className="text-lg font-mono font-bold text-[#8888bb]">
            {(result.ml_scores.pd_30d * 100).toFixed(1)}%
          </p>
        </div>
      </div>
    </motion.div>
  );
}
