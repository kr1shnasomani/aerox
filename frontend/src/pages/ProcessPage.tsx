import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Zap, Play, RotateCcw } from 'lucide-react';
import { processBooking, getScenarios } from '../api/client';
import type { BookingRequest, ProcessingResult, Scenario, CreditOption } from '../types';
import GlassCard from '../components/shared/GlassCard';
import LoadingSpinner from '../components/shared/LoadingSpinner';
import PipelineVisualizer from '../components/pipeline/PipelineVisualizer';
import DecisionBanner from '../components/decision/DecisionBanner';
import OptionsPanel from '../components/decision/OptionsPanel';
import WhatsAppPreview from '../components/decision/WhatsAppPreview';

export default function ProcessPage() {
  const navigate = useNavigate();
  const [scenarios, setScenarios] = useState<Scenario[]>([]);
  const [form, setForm] = useState<BookingRequest>({
    company_id: 'IN-TRV-000567',
    company_name: 'MediumRisk Agency',
    booking_amount: 50000,
    current_outstanding: 45000,
    credit_limit: 80000,
    route: 'Chennai-Dubai',
    booking_date: '2026-02-15',
  });
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<ProcessingResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getScenarios().then(data => setScenarios(data.scenarios)).catch(() => {});
  }, []);

  const handleScenario = (scenario: Scenario) => {
    setForm(scenario.booking);
    setResult(null);
    setError(null);
  };

  const handleProcess = async () => {
    setIsLoading(true);
    setResult(null);
    setError(null);
    try {
      const res = await processBooking(form);
      setResult(res);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Failed to process booking');
    } finally {
      setIsLoading(false);
    }
  };

  const handleReset = () => {
    setResult(null);
    setError(null);
  };

  const handleNegotiate = (option: CreditOption) => {
    if (result) {
      navigate('/negotiate', {
        state: {
          bookingRequest: result.booking_request,
          mlScores: result.ml_scores,
          options: result.options,
          selectedOption: option,
        },
      });
    }
  };

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-white flex items-center gap-3">
          <Zap className="text-[#8b5cf6]" size={24} />
          Process Booking Request
        </h1>
        <p className="text-sm text-[#8888bb] mt-1">Run a booking through the AEROX 4-layer pipeline</p>
      </div>

      {/* Scenario Buttons */}
      <div className="flex gap-3">
        {scenarios.map(s => (
          <button
            key={s.id}
            onClick={() => handleScenario(s)}
            className={`px-4 py-2 rounded-lg text-sm font-medium border transition-all ${
              form.company_id === s.booking.company_id
                ? s.id === 'green' ? 'bg-[#22c55e]/15 border-[#22c55e]/30 text-[#22c55e]' :
                  s.id === 'yellow' ? 'bg-[#eab308]/15 border-[#eab308]/30 text-[#eab308]' :
                  'bg-[#ef4444]/15 border-[#ef4444]/30 text-[#ef4444]'
                : 'border-[#2d2d6b] text-[#8888bb] hover:text-white hover:border-[#555]'
            }`}
          >
            {s.label}
          </button>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: Form */}
        <GlassCard className="lg:col-span-1">
          <h3 className="text-sm font-semibold text-[#8888bb] uppercase tracking-wider mb-4">Booking Details</h3>
          <div className="space-y-3">
            {[
              { label: 'Company ID', key: 'company_id' },
              { label: 'Company Name', key: 'company_name' },
              { label: 'Booking Amount (₹)', key: 'booking_amount', type: 'number' },
              { label: 'Outstanding (₹)', key: 'current_outstanding', type: 'number' },
              { label: 'Credit Limit (₹)', key: 'credit_limit', type: 'number' },
              { label: 'Route', key: 'route' },
            ].map(({ label, key, type }) => (
              <div key={key}>
                <label className="text-xs text-[#666] block mb-1">{label}</label>
                <input
                  type={type || 'text'}
                  value={(form as Record<string, unknown>)[key] as string | number}
                  onChange={e => setForm(prev => ({
                    ...prev,
                    [key]: type === 'number' ? Number(e.target.value) : e.target.value,
                  }))}
                  className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-[#8b5cf6]/50 transition-colors"
                />
              </div>
            ))}

            <div className="flex gap-2 pt-2">
              <button
                onClick={handleProcess}
                disabled={isLoading}
                className="flex-1 flex items-center justify-center gap-2 px-4 py-2.5 bg-[#8b5cf6] hover:bg-[#7c3aed] disabled:opacity-50 rounded-lg text-sm font-medium text-white transition-colors"
              >
                <Play size={14} />
                {isLoading ? 'Processing...' : 'Process'}
              </button>
              {result && (
                <button
                  onClick={handleReset}
                  className="px-3 py-2.5 border border-white/10 rounded-lg text-sm text-[#8888bb] hover:text-white transition-colors"
                >
                  <RotateCcw size={14} />
                </button>
              )}
            </div>
          </div>
        </GlassCard>

        {/* Right: Pipeline + Results */}
        <div className="lg:col-span-2 space-y-6">
          {/* Pipeline visualization */}
          {(isLoading || result) && (
            <GlassCard>
              <PipelineVisualizer result={result} isLoading={isLoading} />
            </GlassCard>
          )}

          {/* Error */}
          {error && (
            <GlassCard>
              <div className="text-[#ef4444] text-sm">
                <p className="font-semibold">Error processing booking</p>
                <p className="text-[#8888bb] mt-1">{error}</p>
              </div>
            </GlassCard>
          )}

          {/* Decision Banner */}
          {result && <DecisionBanner result={result} />}

          {/* Options (yellow only) */}
          {result?.options && result.options.length > 0 && (
            <GlassCard animate={false}>
              <OptionsPanel
                options={result.options}
                maxEL={5000}
                onSelect={handleNegotiate}
              />
            </GlassCard>
          )}

          {/* WhatsApp Preview */}
          {result?.message && typeof result.message !== 'string' && result.message.body && (
            <GlassCard animate={false}>
              <WhatsAppPreview message={result.message} />
            </GlassCard>
          )}

          {/* Risk Assessment */}
          {result?.risk_assessment && (
            <GlassCard>
              <h3 className="text-sm font-semibold text-[#8888bb] uppercase tracking-wider mb-3">Risk Assessment</h3>
              <p className="text-sm text-[#e2e2ff] leading-relaxed">{result.risk_assessment.risk_summary}</p>
              {result.risk_assessment.key_risk_factors && result.risk_assessment.key_risk_factors.length > 0 && (
                <div className="mt-3">
                  <p className="text-xs text-[#666] mb-1">Key Risk Factors</p>
                  <ul className="space-y-1">
                    {result.risk_assessment.key_risk_factors.map((f, i) => (
                      <li key={i} className="text-xs text-[#ef4444] flex items-start gap-2">
                        <span className="mt-1 w-1.5 h-1.5 rounded-full bg-[#ef4444] flex-shrink-0" />
                        {f}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              {result.risk_assessment.mitigating_factors && result.risk_assessment.mitigating_factors.length > 0 && (
                <div className="mt-3">
                  <p className="text-xs text-[#666] mb-1">Mitigating Factors</p>
                  <ul className="space-y-1">
                    {result.risk_assessment.mitigating_factors.map((f, i) => (
                      <li key={i} className="text-xs text-[#22c55e] flex items-start gap-2">
                        <span className="mt-1 w-1.5 h-1.5 rounded-full bg-[#22c55e] flex-shrink-0" />
                        {f}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              <p className="text-sm text-[#8b5cf6] mt-3 font-medium">{result.risk_assessment.recommendation}</p>
            </GlassCard>
          )}

          {/* Placeholder when nothing has been run */}
          {!isLoading && !result && !error && (
            <GlassCard>
              <div className="text-center py-12">
                <Zap size={48} className="mx-auto text-[#2d2d6b] mb-4" />
                <p className="text-[#8888bb]">Select a scenario or fill in booking details, then click Process</p>
                <p className="text-xs text-[#555] mt-2">The pipeline will animate as it processes through all 4 layers</p>
              </div>
            </GlassCard>
          )}
        </div>
      </div>
    </div>
  );
}
