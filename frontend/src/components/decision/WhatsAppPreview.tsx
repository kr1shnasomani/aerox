import { motion } from 'framer-motion';
import { Phone } from 'lucide-react';

interface WhatsAppPreviewProps {
  message: { subject: string; body: string; cta_buttons?: string[] } | string;
}

export default function WhatsAppPreview({ message }: WhatsAppPreviewProps) {
  const isString = typeof message === 'string';
  const body = isString ? message : message.body;
  const buttons = isString ? [] : (message.cta_buttons || []);

  // Format body: replace **text** with bold spans
  const formatBody = (text: string) => {
    return text.split('\n').map((line, i) => {
      const parts = line.split(/(\*\*.*?\*\*)/g);
      return (
        <span key={i}>
          {parts.map((part, j) => {
            if (part.startsWith('**') && part.endsWith('**')) {
              return <strong key={j} className="text-white">{part.slice(2, -2)}</strong>;
            }
            return <span key={j}>{part}</span>;
          })}
          {i < text.split('\n').length - 1 && <br />}
        </span>
      );
    });
  };

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ delay: 0.3 }}
    >
      <h3 className="text-sm font-semibold text-[#8888bb] uppercase tracking-wider mb-4">
        WhatsApp Preview
      </h3>
      {/* Phone frame */}
      <div className="max-w-sm mx-auto">
        <div className="rounded-[2rem] border-4 border-[#333] bg-[#111] overflow-hidden shadow-2xl">
          {/* Notch */}
          <div className="h-6 bg-[#111] flex items-center justify-center">
            <div className="w-20 h-3 bg-[#222] rounded-full" />
          </div>

          {/* WhatsApp header */}
          <div className="bg-[#075e54] px-4 py-3 flex items-center gap-3">
            <div className="w-8 h-8 rounded-full bg-[#128c7e] flex items-center justify-center">
              <Phone size={14} className="text-white" />
            </div>
            <div>
              <p className="text-white text-sm font-semibold">AEROX Credit Team</p>
              <p className="text-[#aad] text-[10px]">Business Account</p>
            </div>
          </div>

          {/* Chat area */}
          <div className="bg-[#0b141a] p-4 min-h-[300px] max-h-[400px] overflow-y-auto" style={{ backgroundImage: 'url("data:image/svg+xml,%3Csvg width=\'200\' height=\'200\' xmlns=\'http://www.w3.org/2000/svg\'%3E%3Cpath d=\'M100 0L200 100L100 200L0 100z\' fill=\'none\' stroke=\'%23ffffff08\' stroke-width=\'0.5\'/%3E%3C/svg%3E")' }}>
            {/* Message bubble */}
            <div className="bg-[#005c4b] rounded-lg rounded-tl-none p-3 max-w-[85%] shadow-md">
              <p className="text-[#e9edef] text-sm leading-relaxed whitespace-pre-wrap">
                {formatBody(body)}
              </p>
              <p className="text-[#ffffff60] text-[10px] text-right mt-2">
                {new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              </p>
            </div>

            {/* CTA buttons */}
            {buttons.length > 0 && (
              <div className="mt-2 space-y-1">
                {buttons.map((btn, i) => (
                  <div key={i} className="bg-[#005c4b] rounded-lg p-2.5 text-center cursor-pointer hover:bg-[#006d5b] transition-colors">
                    <span className="text-[#53bdeb] text-sm font-medium">{btn}</span>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Input bar */}
          <div className="bg-[#1f2c33] px-3 py-2 flex items-center gap-2">
            <div className="flex-1 bg-[#2a3942] rounded-full px-4 py-2">
              <p className="text-[#8696a0] text-sm">Reply A, B, or C...</p>
            </div>
            <div className="w-10 h-10 rounded-full bg-[#00a884] flex items-center justify-center">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="white"><path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/></svg>
            </div>
          </div>

          {/* Bottom bar */}
          <div className="h-4 bg-[#111]" />
        </div>
      </div>
    </motion.div>
  );
}
