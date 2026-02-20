import { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Shield, Brain, Clock, Calculator, FileText, MessageSquare, CheckCircle, XCircle, AlertTriangle, Activity } from 'lucide-react';
import type { ProcessingResult } from '../../types';

interface PipelineVisualizerProps {
  result: ProcessingResult | null;
  isLoading: boolean;
}

interface Step {
  id: string;
  name: string;
  description: string;
  icon: React.ElementType;
  duration: string;
  status: 'pending' | 'active' | 'complete' | 'skipped';
  data?: string;
}

const baseSteps: Omit<Step, 'status' | 'data'>[] = [
  { id: 'l0', name: 'Layer 0: Access Intelligence', description: 'Session validation & ATO detection', icon: Shield, duration: '10ms' },
  { id: 'l1', name: 'Layer 1: Intent Detection', description: 'Causal GNN fraud intent scoring', icon: Brain, duration: '30ms' },
  { id: 'l2', name: 'Layer 2: Capacity Assessment', description: 'Survival model credit analysis', icon: Clock, duration: '40ms' },
  { id: 'gate', name: 'Decision Gate', description: 'Intent vs Capacity routing', icon: Activity, duration: '—' },
  { id: 'fin', name: 'Financial Analysis', description: 'EAD & Expected Loss calculation', icon: Calculator, duration: '10ms' },
  { id: 'risk', name: 'Risk AI Narrative', description: 'LLM risk assessment generation', icon: FileText, duration: '1-2s' },
  { id: 'terms', name: 'Terms Crafter', description: '3-option generation with compliance', icon: AlertTriangle, duration: '20ms' },
  { id: 'comms', name: 'Communication Agent', description: 'WhatsApp message generation', icon: MessageSquare, duration: '1-2s' },
];

export default function PipelineVisualizer({ result, isLoading }: PipelineVisualizerProps) {
  const [currentStep, setCurrentStep] = useState(-1);
  const [steps, setSteps] = useState<Step[]>(
    baseSteps.map(s => ({ ...s, status: 'pending' as const }))
  );

  useEffect(() => {
    if (!isLoading && !result) {
      setCurrentStep(-1);
      setSteps(baseSteps.map(s => ({ ...s, status: 'pending' as const })));
      return;
    }

    if (isLoading) {
      setCurrentStep(0);
      setSteps(baseSteps.map(s => ({ ...s, status: 'pending' as const })));

      // Animate steps progressively
      const delays = [0, 500, 1000, 1800, 2400, 3000, 3800, 4500];
      const timers: NodeJS.Timeout[] = [];

      delays.forEach((delay, i) => {
        timers.push(setTimeout(() => {
          setCurrentStep(i);
          setSteps(prev => prev.map((s, j) => ({
            ...s,
            status: j < i ? 'complete' : j === i ? 'active' : 'pending'
          })));
        }, delay));
      });

      return () => timers.forEach(clearTimeout);
    }
  }, [isLoading]);

  // When result arrives, finalize steps
  useEffect(() => {
    if (!result) return;

    const isGreen = result.risk_category === 'green';
    const isRed = result.risk_category === 'red' && result.decision === 'BLOCKED';

    setSteps(prev => prev.map((s, i) => {
      // Layer 0-2 + gate always complete
      if (i <= 3) {
        let data: string | undefined;
        if (i === 0) data = 'Session clean - no ATO detected';
        if (i === 1) data = `Intent Score: ${result.ml_scores.intent_score.toFixed(3)}`;
        if (i === 2) data = `Capacity Score: ${result.ml_scores.capacity_score.toFixed(3)} | PD(7d): ${(result.ml_scores.pd_7d * 100).toFixed(1)}%, PD(30d): ${(result.ml_scores.pd_30d * 100).toFixed(1)}%`;
        if (i === 3) data = `${result.risk_category.toUpperCase()} FLAG → ${result.decision}`;
        return { ...s, status: 'complete', data };
      }

      // Skip steps 4-7 for green/red
      if (isGreen || isRed) {
        return { ...s, status: 'skipped' };
      }

      // Yellow flow — complete all
      let data: string | undefined;
      if (i === 4 && result.financial_analysis) {
        data = `Exposure: ₹${result.financial_analysis.total_exposure?.toLocaleString()} | EL(30d): ₹${result.financial_analysis.baseline_el_30d?.toLocaleString()}`;
      }
      if (i === 5 && result.risk_assessment) {
        data = result.risk_assessment.recommendation || result.risk_assessment.risk_summary?.slice(0, 80);
      }
      if (i === 6 && result.options) {
        data = `${result.options.length} compliant options generated`;
      }
      if (i === 7 && result.message) {
        data = typeof result.message === 'string' ? 'Message ready' : `Subject: ${result.message.subject}`;
      }
      return { ...s, status: 'complete', data };
    }));
    setCurrentStep(7);
  }, [result]);

  if (currentStep === -1 && !result) return null;

  return (
    <div className="space-y-2">
      <h3 className="text-sm font-semibold text-[#8888bb] uppercase tracking-wider mb-4">Processing Pipeline</h3>
      {steps.map((step, i) => {
        const Icon = step.icon;
        const isActive = step.status === 'active';
        const isComplete = step.status === 'complete';
        const isSkipped = step.status === 'skipped';
        const isGate = step.id === 'gate';

        return (
          <AnimatePresence key={step.id}>
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: isSkipped ? 0.3 : 1, x: 0 }}
              transition={{ delay: i * 0.08, duration: 0.3 }}
              className={`flex items-start gap-4 p-3 rounded-lg transition-all ${
                isActive ? 'bg-[#8b5cf6]/10 border border-[#8b5cf6]/30' :
                isComplete && isGate ? (
                  result?.risk_category === 'green' ? 'bg-[#22c55e]/10 border border-[#22c55e]/30' :
                  result?.risk_category === 'red' ? 'bg-[#ef4444]/10 border border-[#ef4444]/30' :
                  'bg-[#eab308]/10 border border-[#eab308]/30'
                ) :
                isComplete ? 'bg-white/[0.02] border border-white/5' :
                'border border-transparent'
              }`}
            >
              {/* Icon */}
              <div className={`mt-0.5 flex-shrink-0 w-8 h-8 rounded-lg flex items-center justify-center ${
                isActive ? 'bg-[#8b5cf6]/20 text-[#8b5cf6]' :
                isComplete ? (
                  isGate && result?.risk_category === 'green' ? 'bg-[#22c55e]/20 text-[#22c55e]' :
                  isGate && result?.risk_category === 'red' ? 'bg-[#ef4444]/20 text-[#ef4444]' :
                  isGate && result?.risk_category === 'yellow' ? 'bg-[#eab308]/20 text-[#eab308]' :
                  'bg-[#22c55e]/20 text-[#22c55e]'
                ) :
                'bg-white/5 text-[#555]'
              }`}>
                {isActive ? (
                  <motion.div animate={{ rotate: 360 }} transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}>
                    <Icon size={16} />
                  </motion.div>
                ) : isComplete ? (
                  <CheckCircle size={16} />
                ) : isSkipped ? (
                  <XCircle size={14} />
                ) : (
                  <Icon size={16} />
                )}
              </div>

              {/* Text */}
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className={`text-sm font-medium ${isComplete || isActive ? 'text-white' : 'text-[#666]'}`}>
                    {step.name}
                  </span>
                  <span className="text-[10px] text-[#555]">{step.duration}</span>
                  {isSkipped && <span className="text-[10px] text-[#555] italic">skipped</span>}
                </div>
                <p className="text-xs text-[#666] mt-0.5">{step.description}</p>
                {step.data && isComplete && (
                  <motion.p
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className={`text-xs mt-1 font-mono ${
                      isGate && result?.risk_category === 'green' ? 'text-[#22c55e]' :
                      isGate && result?.risk_category === 'red' ? 'text-[#ef4444]' :
                      isGate && result?.risk_category === 'yellow' ? 'text-[#eab308]' :
                      'text-[#8b5cf6]'
                    }`}
                  >
                    {step.data}
                  </motion.p>
                )}
              </div>
            </motion.div>
          </AnimatePresence>
        );
      })}
    </div>
  );
}
