import React from 'react';
import { Brain, MapPin, Route, Wallet, ShieldCheck } from 'lucide-react';

const AgentNode = ({ name, state }) => {
  const getIcon = () => {
    switch(name) {
      case 'Orchestrator': return Brain;
      case 'Destination': return MapPin;
      case 'Logistics': return Route;
      case 'Budget': return Wallet;
      case 'Review': return ShieldCheck;
      default: return Brain;
    }
  };
  
  const Icon = getIcon();

  const stateStyles = {
    waiting: 'border-[rgba(122,139,166,0.3)] text-muted opacity-50',
    active: 'border-coral text-coral shadow-glow-coral agent-pulse',
    complete: 'border-cyan text-cyan shadow-glow-cyan transform transition-transform scale-100',
    error: 'border-[#FF3366] text-[#FF3366] agent-shake'
  };

  const baseStyle = "w-[140px] h-[140px] rounded-full bg-surface backdrop-blur-xl border-[1.5px] flex items-center justify-center transition-all duration-500 z-10 relative";

  // for complete scale-in effect, start small and animate
  const scaleClass = state === 'complete' ? 'scale-100' : (state === 'active' ? 'scale-[1.05]' : 'scale-90');

  return (
    <div className="flex flex-col items-center gap-4 relative z-10">
      <div className={`${baseStyle} ${stateStyles[state]} ${state === 'waiting' ? 'scale-90' : ''}`}>
        <Icon size={36} />
      </div>
      <div className="font-heading text-[14px] text-text font-semibold tracking-wide uppercase">
        {name}
      </div>
    </div>
  );
};

export default AgentNode;
