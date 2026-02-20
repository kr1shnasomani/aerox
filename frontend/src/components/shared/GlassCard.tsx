import { motion } from 'framer-motion';

interface GlassCardProps {
  children: React.ReactNode;
  className?: string;
  animate?: boolean;
}

export default function GlassCard({ children, className = '', animate = true }: GlassCardProps) {
  const Wrapper = animate ? motion.div : 'div';
  const props = animate
    ? { initial: { opacity: 0, y: 20 }, animate: { opacity: 1, y: 0 }, transition: { duration: 0.4 } }
    : {};

  return (
    <Wrapper className={`glass-card p-6 ${className}`} {...props}>
      {children}
    </Wrapper>
  );
}
