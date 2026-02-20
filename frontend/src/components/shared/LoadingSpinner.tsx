import { Loader2 } from 'lucide-react';

interface LoadingSpinnerProps {
  text?: string;
  size?: number;
}

export default function LoadingSpinner({ text = 'Processing...', size = 24 }: LoadingSpinnerProps) {
  return (
    <div className="flex flex-col items-center gap-3 py-12">
      <Loader2 size={size} className="animate-spin text-[#8b5cf6]" />
      <p className="text-sm text-[#8888bb]">{text}</p>
    </div>
  );
}
