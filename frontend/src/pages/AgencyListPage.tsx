import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Users, Search, ChevronLeft, ChevronRight } from 'lucide-react';
import { getAgencies } from '../api/client';
import type { Agency } from '../types';
import GlassCard from '../components/shared/GlassCard';
import RiskBadge from '../components/shared/RiskBadge';
import LoadingSpinner from '../components/shared/LoadingSpinner';

export default function AgencyListPage() {
  const navigate = useNavigate();
  const [agencies, setAgencies] = useState<Agency[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [search, setSearch] = useState('');
  const [segment, setSegment] = useState('');
  const [loading, setLoading] = useState(true);

  const fetchAgencies = async () => {
    setLoading(true);
    try {
      const data = await getAgencies({
        page,
        page_size: 20,
        search: search || undefined,
        segment: segment || undefined,
      });
      setAgencies(data.agencies);
      setTotal(data.total);
      setTotalPages(data.total_pages);
    } catch {
      // ignore
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAgencies();
  }, [page, segment]);

  const handleSearch = () => {
    setPage(1);
    fetchAgencies();
  };

  const getRiskCategory = (a: Agency): 'green' | 'yellow' | 'red' => {
    if (a.fraud_flag) return 'red';
    if ((a.risk_score || 0) > 0.6) return 'red';
    if ((a.risk_score || 0) > 0.3) return 'yellow';
    return 'green';
  };

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-white flex items-center gap-3">
          <Users className="text-[#8b5cf6]" size={24} />
          Agencies
        </h1>
        <p className="text-sm text-[#8888bb] mt-1">{total} agencies in dataset</p>
      </div>

      {/* Filters */}
      <div className="flex gap-3">
        <div className="flex-1 relative">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-[#555]" />
          <input
            type="text"
            value={search}
            onChange={e => setSearch(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && handleSearch()}
            placeholder="Search by company ID..."
            className="w-full bg-white/5 border border-white/10 rounded-lg pl-9 pr-3 py-2 text-sm text-white placeholder-[#555] focus:outline-none focus:border-[#8b5cf6]/50"
          />
        </div>
        <select
          value={segment}
          onChange={e => { setSegment(e.target.value); setPage(1); }}
          className="bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-[#8b5cf6]/50"
        >
          <option value="">All Segments</option>
          <option value="micro">Micro</option>
          <option value="small_medium">Small/Medium</option>
          <option value="medium_large">Medium/Large</option>
          <option value="enterprise">Enterprise</option>
        </select>
      </div>

      {/* Table */}
      {loading ? (
        <LoadingSpinner text="Loading agencies..." />
      ) : (
        <GlassCard className="overflow-hidden p-0" animate={false}>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-white/5">
                  {['Company ID', 'Segment', 'Region', 'Credit Util', 'On-Time Rate', 'Chargeback', 'Risk'].map(h => (
                    <th key={h} className="text-left px-4 py-3 text-[10px] text-[#666] uppercase tracking-wider font-medium">
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {agencies.map(a => (
                  <tr
                    key={a.company_id}
                    onClick={() => navigate(`/agencies/${a.company_id}`)}
                    className="border-b border-white/[0.03] hover:bg-white/[0.02] cursor-pointer transition-colors"
                  >
                    <td className="px-4 py-3 font-mono text-[#3b82f6]">{a.company_id}</td>
                    <td className="px-4 py-3 text-[#8888bb] capitalize">{a.segment?.replace('_', ' ')}</td>
                    <td className="px-4 py-3 text-[#8888bb] capitalize">{a.region}</td>
                    <td className="px-4 py-3 font-mono">{((a.credit_utilization || 0) * 100).toFixed(1)}%</td>
                    <td className="px-4 py-3 font-mono">{((a.on_time_payment_rate || 0) * 100).toFixed(1)}%</td>
                    <td className="px-4 py-3 font-mono">{((a.chargeback_rate || 0) * 100).toFixed(2)}%</td>
                    <td className="px-4 py-3"><RiskBadge category={getRiskCategory(a)} size="sm" /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          <div className="flex items-center justify-between px-4 py-3 border-t border-white/5">
            <span className="text-xs text-[#666]">Page {page} of {totalPages}</span>
            <div className="flex gap-2">
              <button
                onClick={() => setPage(p => Math.max(1, p - 1))}
                disabled={page <= 1}
                className="p-1.5 rounded border border-white/10 text-[#8888bb] hover:text-white disabled:opacity-30 transition-colors"
              >
                <ChevronLeft size={14} />
              </button>
              <button
                onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                disabled={page >= totalPages}
                className="p-1.5 rounded border border-white/10 text-[#8888bb] hover:text-white disabled:opacity-30 transition-colors"
              >
                <ChevronRight size={14} />
              </button>
            </div>
          </div>
        </GlassCard>
      )}
    </div>
  );
}
