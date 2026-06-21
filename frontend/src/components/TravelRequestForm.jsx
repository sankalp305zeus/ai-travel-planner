import React, { useState, useEffect } from 'react';
import { Sparkles } from 'lucide-react';

const placeholders = [
  "5 days Tokyo + Kyoto, ₹2,50,000, food and temples, hate crowds",
  "Weekend Amsterdam, fun things, less crowds, 200000",
  "7 days Thailand, Bangkok + Bali, ₹1,50,000, beaches and food"
];

const chips = [
  "🍜 Food tour Tokyo",
  "🏖️ Beach week Bali",
  "🏛️ History trip Rome"
];

const TravelRequestForm = ({ onSubmit }) => {
  const [text, setText] = useState('');
  const [placeholderIdx, setPlaceholderIdx] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setPlaceholderIdx((prev) => (prev + 1) % placeholders.length);
    }, 3500);
    return () => clearInterval(interval);
  }, []);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (text.length > 0 && text.length <= 500) {
      onSubmit(text);
    }
  };

  return (
    <div className="relative z-10 flex flex-col items-center justify-center min-h-screen w-full px-4 animate-in fade-in slide-in-from-bottom-2 duration-500">
      <div className="mb-10 text-center">
        <h1 className="text-4xl md:text-[64px] font-heading font-extrabold bg-gradient-to-br from-white to-cyan bg-clip-text text-transparent mb-4 leading-tight">
          Where shall we wander?
        </h1>
        <p className="text-[18px] font-body text-muted italic">
          Let our agents craft your perfect journey.
        </p>
      </div>
      
      <form onSubmit={handleSubmit} className="w-full max-w-[760px] group">
        <div className="bg-surface backdrop-blur-xl border border-border-strong rounded-[24px] p-8 transition-all duration-400 hover:shadow-glow-cyan">
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder={placeholders[placeholderIdx]}
            className="w-full bg-transparent text-text placeholder-muted text-[17px] font-body outline-none resize-none"
            rows={5}
            maxLength={500}
          />
          
          <div className="flex justify-between items-center mt-6">
            <span className="font-mono text-[12px] text-muted">
              {text.length}/500
            </span>
            <button
              type="submit"
              disabled={text.length === 0 || text.length > 500}
              className="bg-gradient-to-br from-coral to-cyan text-white font-heading font-bold py-[14px] px-[32px] rounded-[12px] shadow-glow-coral transition-all duration-300 hover:scale-[1.04] disabled:opacity-50 disabled:hover:scale-100"
            >
              Plan My Trip ✨
            </button>
          </div>
        </div>
      </form>
      
      <div className="mt-12 flex flex-col items-center">
        <div className="flex items-center gap-2 text-muted text-[12px] uppercase tracking-wider mb-4 font-body">
          <Sparkles size={14} />
          <span>Try one of these</span>
        </div>
        <div className="flex flex-wrap justify-center gap-4">
          {chips.map((chip, idx) => (
            <button
              key={idx}
              onClick={() => setText(chip)}
              className="bg-surface backdrop-blur-md border border-border rounded-full py-[8px] px-[16px] text-[14px] text-text font-body transition-all hover:border-cyan hover:scale-105"
            >
              {chip}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};

export default TravelRequestForm;
