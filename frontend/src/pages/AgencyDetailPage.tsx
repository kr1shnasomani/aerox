import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { ArrowLeft, Zap, Building2 } from 'lucide-react';
import { getAgency } from '../api/client';
import type { Agency } from '../types';
import GlassCard from '../components/shared/GlassCard';
import RiskBadge from '../components/shared/RiskBadge';
import LoadingSpinner from '../components/shared/LoadingSpinner';

export default function AgencyDetailPage() {
  const { companyId } = useParams();
  const navigate = useNavigate();
  const [agency, setAgency] = useState<Agency | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!companyId) return;
    getAgency(companyId)
      .then(data => setAgency(data.agency))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [companyId]);

  if (loading) return <LoadingSpinner text="Loading agency..." />;
  if (!agency) return <div className="text-center py-12 text-[#8888bb]">Agency not found</div>;

  const getRiskCategory = (): 'green' | 'yellow' | 'red' => {
    if (agency.fraud_flag) return 'red';
    if ((agency.risk_score || 0) > 0.6) return 'red';
    if ((agency.risk_score || 0) > 0.3) return 'yellow';
    return 'green';
  };

  const GaugeBar = ({ label, value, max = 1, color }: { label: string; value: number; max?: number; color: string }) => (
    <div>
      <div className="flex justify-between text-xs mb-1">
        <span className="text-[#8888bb]">{label}</span>
        <span className="font-mono text-white">{(value * 100).toFixed(1)}%</span>
      </div>
      <div className="h-2 bg-white/5 rounded-full overflow-hidden">
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${(value / max) * 100}%` }}
          transition={{ duration: 0.8 }}
          className="h-full rounded-full"
          style={{ backgroundColor: color }}
        />
      </div>
    </div>
  );

  const keyMetrics = [
    { label: 'Annual Revenue', value: `₹${(agency.annual_revenue_inr || 0).toLocaleString()}` },
    { label: 'Credit Limit', value: `₹${(agency.credit_limit_inr || 0).toLocaleString()}` },
    { label: 'Outstanding', value: `₹${(agency.current_outstanding_inr || 0).toLocaleString()}` },
    { label: 'Lifetime Bookings', value: String(agency.total_bookings_lifetime || 0) },
    { label: 'Business Age', value: `${agency.business_age_months || 0} months` },
    { label: 'Avg Late Days', value: `${(agency.avg_late_payment_days || 0).toFixed(1)} days` },
  ];

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      {/* Back + Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <button
            onClick={() => navigate('/agencies')}
            className="p-2 rounded-lg border border-white/10 text-[#8888bb] hover:text-white transition-colors"
          >
            <ArrowLeft size={16} />
          </button>
          <div>
            <div className="flex items-center gap-3">
              <Building2 className="text-[#8b5cf6]" size={20} />
              <h1 className="text-xl font-bold text-white font-mono">{agency.company_id}</h1>
              <RiskBadge category={getRiskCategory()} />
            </div>
            <p className="text-sm text-[#8888bb] mt-1 capitalize">
              {agency.segment?.replace('_', ' ')} — {agency.region}
            </p>
          </div>
        </div>
        <button
          onClick={() => navigate('/process', {
            state: {
              prefill: {
                company_id: agency.company_id,
                company_name: agency.company_id,
                booking_amount: Math.round((agency.credit_limit_inr || 50000) * 0.3),
                current_outstanding: agency.current_outstanding_inr || 0,
                credit_limit: agency.credit_limit_inr || 100000,
                route: 'Custom Route',
                booking_date: '2026-02-15',
              },
            },
          })}
          className="flex items-center gap-2 px-4 py-2 bg-[#8b5cf6] hover:bg-[#7c3aed] rounded-lg text-sm font-medium text-white transition-colors"
        >
          <Zap size={14} />
          Process Booking
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Risk Gauges */}
        <GlassCard>
          <h3 className="text-sm font-semibold text-[#8888bb] uppercase tracking-wider mb-4">Risk Profile</h3>
          <div className="space-y-4">
            <GaugeBar label="Credit Utilization" value={agency.credit_utilization || 0} color={((agency.credit_utilization || 0) > 0.7 ? '#ef4444' : (agency.credit_utilization || 0) > 0.4 ? '#eab308' : '#22c55e')} />
            <GaugeBar label="On-Time Payment Rate" value={agency.on_time_payment_rate || 0} color={((agency.on_time_payment_rate || 0) > 0.85 ? '#22c55e' : (agency.on_time_payment_rate || 0) > 0.7 ? '#eab308' : '#ef4444')} />
            <GaugeBar label="Risk Score" value={agency.risk_score || 0} color={((agency.risk_score || 0) > 0.6 ? '#ef4444' : (agency.risk_score || 0) > 0.3 ? '#eab308' : '#22c55e')} />
            <GaugeBar label="Chargeback Rate" value={agency.chargeback_rate || 0} max={0.1} color={((agency.chargeback_rate || 0) > 0.05 ? '#ef4444' : '#22c55e')} />
          </div>

          <div className="flex gap-4 mt-4 pt-4 border-t border-white/5">
            <div className={`flex-1 p-3 rounded-lg text-center ${agency.fraud_flag ? 'bg-[#ef4444]/10 border border-[#ef4444]/20' : 'bg-[#22c55e]/10 border border-[#22c55e]/20'}`}>
              <p className="text-[10px] text-[#666] uppercase">Fraud Flag</p>
              <p className={`text-lg font-bold ${agency.fraud_flag ? 'text-[#ef4444]' : 'text-[#22c55e]'}`}>
                {agency.fraud_flag ? 'YES' : 'NO'}
              </p>
            </div>
            <div className={`flex-1 p-3 rounded-lg text-center ${agency.default_flag ? 'bg-[#ef4444]/10 border border-[#ef4444]/20' : 'bg-[#22c55e]/10 border border-[#22c55e]/20'}`}>
              <p className="text-[10px] text-[#666] uppercase">Default Flag</p>
              <p className={`text-lg font-bold ${agency.default_flag ? 'text-[#ef4444]' : 'text-[#22c55e]'}`}>
                {agency.default_flag ? 'YES' : 'NO'}
              </p>
            </div>
          </div>
        </GlassCard>

        {/* Key Metrics */}
        <GlassCard>
          <h3 className="text-sm font-semibold text-[#8888bb] uppercase tracking-wider mb-4">Key Metrics</h3>
          <div className="grid grid-cols-2 gap-4">
            {keyMetrics.map(m => (
              <div key={m.label} className="p-3 rounded-lg bg-white/[0.02] border border-white/5">
                <p className="text-[10px] text-[#666] uppercase">{m.label}</p>
                <p className="text-lg font-bold text-white mt-1 font-mono">{m.value}</p>
              </div>
            ))}
          </div>
        </GlassCard>
      </div>
    </div>
  );
}
