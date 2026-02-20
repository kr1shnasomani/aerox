import { useState, useEffect, useRef } from 'react';
import { useLocation } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Send, AlertTriangle, MessageSquare, RotateCcw } from 'lucide-react';
import { negotiate, resetNegotiation, getScenarios } from '../api/client';
import type { NegotiationResult, CreditOption } from '../types';
import GlassCard from '../components/shared/GlassCard';

interface ChatMessage {
  role: 'user' | 'agent' | 'system';
  content: string;
  offer?: NegotiationResult['offer'];
  expectedLoss?: number | null;
}

export default function NegotiatePage() {
  const location = useLocation();
  const state = location.state as {
    bookingRequest?: Record<string, unknown>;
    mlScores?: Record<string, unknown>;
    options?: CreditOption[];
  } | null;

  const [bookingRequest, setBookingRequest] = useState<Record<string, unknown>>(
    state?.bookingRequest || {
      company_id: 'IN-TRV-000567',
      company_name: 'MediumRisk Agency',
      booking_amount: 50000,
      current_outstanding: 45000,
      credit_limit: 80000,
      route: 'Chennai-Dubai',
      booking_date: '2026-02-15',
    }
  );
  const [mlScores, setMlScores] = useState<Record<string, unknown>>(
    state?.mlScores || { intent_score: 0.32, capacity_score: 0.55, pd_7d: 0.02, pd_14d: 0.08, pd_30d: 0.15 }
  );
  const [options, setOptions] = useState<CreditOption[]>(state?.options || []);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [round, setRound] = useState(1);
  const [isLoading, setIsLoading] = useState(false);
  const [isComplete, setIsComplete] = useState(false);
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const chatEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    getScenarios().then(data => setSuggestions(data.negotiation_messages)).catch(() => {});
    resetNegotiation().catch(() => {});

    // Initial system message
    setMessages([
      {
        role: 'system',
        content: `Negotiation started for ${(bookingRequest.company_name as string) || 'Agency'}. Booking: ₹${Number(bookingRequest.booking_amount || 0).toLocaleString()}. You have 3 rounds to reach an agreement.`,
      },
    ]);
  }, []);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async (text?: string) => {
    const msg = text || input;
    if (!msg.trim() || isLoading || isComplete) return;

    setInput('');
    setMessages(prev => [...prev, { role: 'user', content: msg }]);
    setIsLoading(true);

    try {
      const result = await negotiate(msg, round, bookingRequest, mlScores, options as unknown as Record<string, unknown>[]);

      setMessages(prev => [
        ...prev,
        {
          role: 'agent',
          content: result.response,
          offer: result.offer,
          expectedLoss: result.expected_loss,
        },
      ]);

      if (result.escalate || round >= 3) {
        setIsComplete(true);
        if (result.escalate) {
          setMessages(prev => [
            ...prev,
            { role: 'system', content: 'Escalated to manual review. A senior credit team member will review within 2 hours.' },
          ]);
        }
      }

      setRound(r => r + 1);
    } catch {
      setMessages(prev => [...prev, { role: 'system', content: 'Failed to get response. Please try again.' }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleReset = async () => {
    await resetNegotiation().catch(() => {});
    setRound(1);
    setIsComplete(false);
    setMessages([
      {
        role: 'system',
        content: `Negotiation restarted for ${(bookingRequest.company_name as string) || 'Agency'}. Booking: ₹${Number(bookingRequest.booking_amount || 0).toLocaleString()}. You have 3 rounds.`,
      },
    ]);
  };

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-3">
            <MessageSquare className="text-[#8b5cf6]" size={24} />
            Credit Negotiation
          </h1>
          <p className="text-sm text-[#8888bb] mt-1">
            Interactive 3-round negotiation with the AEROX agent
          </p>
        </div>
        <div className="flex items-center gap-3">
          <span className={`text-sm font-mono px-3 py-1 rounded-full border ${
            round > 3 || isComplete
              ? 'border-[#ef4444]/30 text-[#ef4444] bg-[#ef4444]/10'
              : 'border-[#8b5cf6]/30 text-[#8b5cf6] bg-[#8b5cf6]/10'
          }`}>
            Round {Math.min(round, 3)}/3
          </span>
          <button
            onClick={handleReset}
            className="p-2 rounded-lg border border-white/10 text-[#8888bb] hover:text-white transition-colors"
          >
            <RotateCcw size={16} />
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Context sidebar */}
        <GlassCard className="lg:col-span-1">
          <h3 className="text-xs font-semibold text-[#8888bb] uppercase tracking-wider mb-3">Context</h3>
          <div className="space-y-2 text-xs">
            <div className="flex justify-between">
              <span className="text-[#666]">Company</span>
              <span className="text-white font-medium">{bookingRequest.company_name as string}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-[#666]">Booking</span>
              <span className="text-white font-mono">₹{Number(bookingRequest.booking_amount || 0).toLocaleString()}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-[#666]">Outstanding</span>
              <span className="text-white font-mono">₹{Number(bookingRequest.current_outstanding || 0).toLocaleString()}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-[#666]">Intent</span>
              <span className="text-[#22c55e] font-mono">{Number(mlScores.intent_score || 0).toFixed(3)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-[#666]">Capacity</span>
              <span className="text-[#eab308] font-mono">{Number(mlScores.capacity_score || 0).toFixed(3)}</span>
            </div>
            <div className="border-t border-white/5 pt-2 mt-2">
              <span className="text-[#666]">Max EL</span>
              <span className="text-[#ef4444] font-mono ml-2">₹5,000</span>
            </div>
            <div>
              <span className="text-[#666]">LGD</span>
              <span className="text-white font-mono ml-2">0.70</span>
            </div>
          </div>

          {options.length > 0 && (
            <div className="mt-4 pt-4 border-t border-white/5">
              <h4 className="text-[10px] text-[#666] uppercase mb-2">Initial Options</h4>
              {options.map(opt => (
                <div key={opt.option_id} className="text-[10px] text-[#8888bb] py-1">
                  <span className="text-white font-medium">Opt {opt.option_id}:</span> {opt.settlement_days}d, ₹{opt.upfront_amount.toLocaleString()} up, EL=₹{opt.expected_loss.toLocaleString()}
                </div>
              ))}
            </div>
          )}
        </GlassCard>

        {/* Chat area */}
        <div className="lg:col-span-3 flex flex-col">
          <GlassCard className="flex-1 flex flex-col min-h-[500px]" animate={false}>
            {/* Messages */}
            <div className="flex-1 overflow-y-auto space-y-4 mb-4 max-h-[500px]">
              {messages.map((msg, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  {msg.role === 'system' ? (
                    <div className="flex items-center gap-2 px-4 py-2 rounded-lg bg-[#8b5cf6]/10 border border-[#8b5cf6]/20 text-xs text-[#8b5cf6] max-w-[80%]">
                      <AlertTriangle size={12} />
                      {msg.content}
                    </div>
                  ) : (
                    <div className={`max-w-[75%] rounded-xl px-4 py-3 ${
                      msg.role === 'user'
                        ? 'bg-[#3b82f6] text-white rounded-br-sm'
                        : 'bg-white/[0.04] border border-white/5 text-[#e2e2ff] rounded-bl-sm'
                    }`}>
                      <p className="text-sm whitespace-pre-wrap leading-relaxed">{msg.content}</p>

                      {/* Offer card */}
                      {msg.offer && (
                        <div className="mt-3 p-3 rounded-lg bg-white/5 border border-white/10">
                          <p className="text-[10px] text-[#666] uppercase mb-1">Counter-Offer</p>
                          <div className="grid grid-cols-3 gap-2 text-xs">
                            <div>
                              <span className="text-[#666]">Upfront</span>
                              <p className="text-white font-mono">₹{msg.offer.upfront.toLocaleString()}</p>
                            </div>
                            <div>
                              <span className="text-[#666]">Days</span>
                              <p className="text-white font-mono">{msg.offer.settlement_days}</p>
                            </div>
                            <div>
                              <span className="text-[#666]">Amount</span>
                              <p className="text-white font-mono">₹{msg.offer.approved_amount.toLocaleString()}</p>
                            </div>
                          </div>
                          {msg.expectedLoss != null && (
                            <p className="text-[10px] text-[#eab308] mt-2 font-mono">
                              EL = ₹{msg.expectedLoss.toLocaleString()}
                            </p>
                          )}
                        </div>
                      )}
                    </div>
                  )}
                </motion.div>
              ))}
              {isLoading && (
                <div className="flex justify-start">
                  <div className="bg-white/[0.04] border border-white/5 rounded-xl px-4 py-3 rounded-bl-sm">
                    <div className="flex gap-1">
                      {[0, 1, 2].map(i => (
                        <motion.div
                          key={i}
                          className="w-2 h-2 rounded-full bg-[#8b5cf6]"
                          animate={{ opacity: [0.3, 1, 0.3] }}
                          transition={{ duration: 1, repeat: Infinity, delay: i * 0.2 }}
                        />
                      ))}
                    </div>
                  </div>
                </div>
              )}
              <div ref={chatEndRef} />
            </div>

            {/* Suggestions */}
            {messages.length <= 2 && suggestions.length > 0 && (
              <div className="flex flex-wrap gap-2 mb-3">
                {suggestions.map((s, i) => (
                  <button
                    key={i}
                    onClick={() => handleSend(s)}
                    disabled={isLoading}
                    className="px-3 py-1.5 rounded-full text-xs text-[#8888bb] border border-white/10 hover:text-white hover:border-[#8b5cf6]/30 transition-all"
                  >
                    {s}
                  </button>
                ))}
              </div>
            )}

            {/* Input */}
            <div className="flex gap-2">
              <input
                type="text"
                value={input}
                onChange={e => setInput(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && handleSend()}
                placeholder={isComplete ? 'Negotiation complete' : 'Type your counter-proposal...'}
                disabled={isComplete || isLoading}
                className="flex-1 bg-white/5 border border-white/10 rounded-lg px-4 py-2.5 text-sm text-white placeholder-[#555] focus:outline-none focus:border-[#8b5cf6]/50 disabled:opacity-50 transition-colors"
              />
              <button
                onClick={() => handleSend()}
                disabled={!input.trim() || isComplete || isLoading}
                className="px-4 py-2.5 bg-[#8b5cf6] hover:bg-[#7c3aed] disabled:opacity-30 rounded-lg text-white transition-colors"
              >
                <Send size={16} />
              </button>
            </div>
          </GlassCard>
        </div>
      </div>
    </div>
  );
}
