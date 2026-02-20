import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { BarChart3, Users, Shield, TrendingUp, AlertTriangle, Zap } from 'lucide-react';
import { PieChart, Pie, Cell, ResponsiveContainer, ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip, ReferenceArea, ReferenceLine } from 'recharts';
import { getStats, getConfig, getAgencies } from '../api/client';
import type { Stats, DecisionConfig, Agency } from '../types';
import GlassCard from '../components/shared/GlassCard';
import LoadingSpinner from '../components/shared/LoadingSpinner';

export default function DashboardPage() {
  const navigate = useNavigate();
  const [stats, setStats] = useState<Stats | null>(null);
  const [config, setConfig] = useState<DecisionConfig | null>(null);
  const [agencies, setAgencies] = useState<Agency[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([getStats(), getConfig(), getAgencies({ page_size: 200 })])
      .then(([s, c, a]) => {
        setStats(s);
        setConfig(c);
        setAgencies(a.agencies);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <LoadingSpinner text="Loading dashboard..." />;

  // Decision distribution for pie chart
  const decisionData = stats ? [
    { name: 'Auto-Approve', value: Math.round(stats.total_agencies * (1 - stats.fraud_rate - stats.default_rate * 0.5)), color: '#22c55e' },
    { name: 'Negotiate', value: Math.round(stats.total_agencies * stats.default_rate * 0.5), color: '#eab308' },
    { name: 'Block', value: Math.round(stats.total_agencies * stats.fraud_rate), color: '#ef4444' },
  ] : [];

  // Quadrant data - use risk_score and on_time_payment_rate as proxies
  const quadrantData = agencies
    .filter(a => a.risk_score != null && a.on_time_payment_rate != null)
    .map(a => ({
      x: Math.min(1, Math.max(0, (a.risk_score || 0))),
      y: Math.min(1, Math.max(0, (a.on_time_payment_rate || 0))),
      id: a.company_id,
      fraud: a.fraud_flag,
    }));

  const metrics = stats ? [
    { label: 'Total Agencies', value: stats.total_agencies.toLocaleString(), icon: Users, color: 'text-[#3b82f6]' },
    { label: 'Avg Credit Util', value: `${(stats.avg_credit_utilization * 100).toFixed(1)}%`, icon: BarChart3, color: 'text-[#8b5cf6]' },
    { label: 'On-Time Rate', value: `${(stats.avg_on_time_payment_rate * 100).toFixed(1)}%`, icon: TrendingUp, color: 'text-[#22c55e]' },
    { label: 'Fraud Rate', value: `${(stats.fraud_rate * 100).toFixed(1)}%`, icon: Shield, color: 'text-[#ef4444]' },
  ] : [];

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Dashboard</h1>
          <p className="text-sm text-[#8888bb] mt-1">AEROX Risk Intelligence Overview</p>
        </div>
        <button
          onClick={() => navigate('/process')}
          className="flex items-center gap-2 px-4 py-2 bg-[#8b5cf6] hover:bg-[#7c3aed] rounded-lg text-sm font-medium text-white transition-colors"
        >
          <Zap size={14} />
          Process Booking
        </button>
      </div>

      {/* Metric Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {metrics.map((m, i) => (
          <motion.div
            key={m.label}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.1 }}
            className="glass-card p-5"
          >
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs text-[#666] uppercase">{m.label}</span>
              <m.icon size={16} className={m.color} />
            </div>
            <p className="text-2xl font-bold text-white">{m.value}</p>
          </motion.div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Risk Quadrant Chart */}
        <GlassCard className="lg:col-span-2">
          <h3 className="text-sm font-semibold text-[#8888bb] uppercase tracking-wider mb-4">
            Risk Quadrant — Intent vs Capacity Proxy
          </h3>
          <ResponsiveContainer width="100%" height={350}>
            <ScatterChart margin={{ top: 10, right: 10, bottom: 30, left: 10 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#2d2d6b" />
              <XAxis
                type="number"
                dataKey="x"
                domain={[0, 1]}
                name="Risk Score (Intent Proxy)"
                tick={{ fill: '#8888bb', fontSize: 11 }}
                label={{ value: 'Risk Score (Intent Proxy)', position: 'bottom', fill: '#666', fontSize: 11 }}
              />
              <YAxis
                type="number"
                dataKey="y"
                domain={[0, 1]}
                name="On-Time Rate (Capacity Proxy)"
                tick={{ fill: '#8888bb', fontSize: 11 }}
                label={{ value: 'On-Time Rate', angle: -90, position: 'insideLeft', fill: '#666', fontSize: 11 }}
              />
              {config && (
                <>
                  {/* Green zone: low risk, high capacity */}
                  <ReferenceArea x1={0} x2={config.decision_matrix.approve_intent_threshold} y1={config.decision_matrix.approve_capacity_threshold} y2={1} fill="#22c55e" fillOpacity={0.05} />
                  {/* Red zone: high risk */}
                  <ReferenceArea x1={config.decision_matrix.block_intent_threshold} x2={1} y1={0} y2={1} fill="#ef4444" fillOpacity={0.05} />
                  {/* Threshold lines */}
                  <ReferenceLine x={config.decision_matrix.approve_intent_threshold} stroke="#eab308" strokeDasharray="5 5" label={{ value: 'Intent 0.40', fill: '#eab308', fontSize: 10 }} />
                  <ReferenceLine x={config.decision_matrix.block_intent_threshold} stroke="#ef4444" strokeDasharray="5 5" label={{ value: 'Intent 0.60', fill: '#ef4444', fontSize: 10 }} />
                  <ReferenceLine y={config.decision_matrix.approve_capacity_threshold} stroke="#22c55e" strokeDasharray="5 5" />
                </>
              )}
              <Tooltip
                content={({ payload }) => {
                  if (!payload?.length) return null;
                  const d = payload[0].payload;
                  return (
                    <div className="bg-[#1a1a3e] border border-[#2d2d6b] rounded-lg p-3 text-xs">
                      <p className="text-white font-mono">{d.id}</p>
                      <p className="text-[#8888bb]">Risk: {d.x.toFixed(3)} | Capacity: {d.y.toFixed(3)}</p>
                    </div>
                  );
                }}
              />
              <Scatter
                data={quadrantData.filter(d => !d.fraud)}
                fill="#3b82f6"
                fillOpacity={0.6}
                r={3}
              />
              <Scatter
                data={quadrantData.filter(d => d.fraud)}
                fill="#ef4444"
                fillOpacity={0.8}
                r={4}
              />
            </ScatterChart>
          </ResponsiveContainer>
          <div className="flex items-center gap-4 mt-2 text-[10px] text-[#666]">
            <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-[#3b82f6]" /> Legitimate</span>
            <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-[#ef4444]" /> Fraud Flagged</span>
          </div>
        </GlassCard>

        {/* Decision Distribution */}
        <GlassCard>
          <h3 className="text-sm font-semibold text-[#8888bb] uppercase tracking-wider mb-4">
            Decision Distribution
          </h3>
          <ResponsiveContainer width="100%" height={250}>
            <PieChart>
              <Pie
                data={decisionData}
                cx="50%"
                cy="50%"
                innerRadius={60}
                outerRadius={90}
                dataKey="value"
                stroke="none"
              >
                {decisionData.map((entry, i) => (
                  <Cell key={i} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip
                content={({ payload }) => {
                  if (!payload?.length) return null;
                  const d = payload[0];
                  return (
                    <div className="bg-[#1a1a3e] border border-[#2d2d6b] rounded-lg p-3 text-xs">
                      <p className="text-white">{d.name}: {String(d.value)}</p>
                    </div>
                  );
                }}
              />
            </PieChart>
          </ResponsiveContainer>
          <div className="space-y-2">
            {decisionData.map(d => (
              <div key={d.name} className="flex items-center justify-between text-sm">
                <div className="flex items-center gap-2">
                  <span className="w-3 h-3 rounded-sm" style={{ backgroundColor: d.color }} />
                  <span className="text-[#8888bb]">{d.name}</span>
                </div>
                <span className="text-white font-mono">{d.value}</span>
              </div>
            ))}
          </div>
        </GlassCard>
      </div>

      {/* Segment breakdown */}
      {stats && Object.keys(stats.segments).length > 0 && (
        <GlassCard>
          <h3 className="text-sm font-semibold text-[#8888bb] uppercase tracking-wider mb-4">
            Agency Segments
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {Object.entries(stats.segments).map(([seg, count]) => (
              <div key={seg} className="p-4 rounded-lg bg-white/[0.02] border border-white/5">
                <p className="text-xs text-[#666] capitalize">{seg.replace('_', ' ')}</p>
                <p className="text-xl font-bold text-white mt-1">{count}</p>
              </div>
            ))}
          </div>
        </GlassCard>
      )}
    </div>
  );
}
