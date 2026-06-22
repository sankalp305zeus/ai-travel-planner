import React, { useState, useEffect } from 'react';
import { Sparkles, Route, TrendingUp, History } from 'lucide-react';
import { motion } from 'framer-motion';

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

const featuredRoutes = {
  "Tokyo Night Food Tour": "5 days Tokyo, ₹2,00,000, street food and nightlife, no crowds",
  "Iceland Ring Road": "8 days Iceland Ring Road, $3000, landscapes and hot springs",
  "Bali Beach Hop": "7 days Bali, ₹1,50,000, beaches and surfing, relaxed pace"
};

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
    <div className="relative z-10 flex flex-col items-center justify-center min-h-screen w-full px-4 overflow-hidden">
      
      {/* Left side: subtle floating stats widget */}
      <motion.div 
        initial={{ opacity: 0, x: -50 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ delay: 0.5, duration: 0.8 }}
        className="hidden 2xl:flex absolute left-8 bottom-1/4 bg-surface backdrop-blur-2xl border border-cyan/20 rounded-full px-4 py-2 items-center gap-2 shadow-glow-cyan"
      >
        <TrendingUp size={16} className="text-cyan" />
        <span className="font-heading text-[13px] font-semibold text-text">20.0K trips planned</span>
      </motion.div>

      {/* Right side: floating "Featured Routes" glass pill stack */}
      <motion.div 
        initial={{ opacity: 0, x: 50 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ delay: 0.6, duration: 0.8 }}
        className="hidden 2xl:flex absolute right-8 top-1/4 flex-col bg-surface backdrop-blur-2xl border border-cyan/20 rounded-[20px] p-5 w-[240px] shadow-[0_0_30px_rgba(255,51,102,0.15)]"
      >
        <div className="flex items-center gap-2 mb-4">
          <Route size={16} className="text-coral" />
          <h3 className="font-heading text-[14px] font-semibold text-coral uppercase tracking-wider">Featured Routes</h3>
        </div>
        <div className="flex flex-col gap-3">
          {Object.entries(featuredRoutes).map(([route, prompt], i) => (
            <div 
              key={i} 
              onClick={() => setText(prompt)}
              className="px-3 py-2 rounded-lg border border-border hover:border-cyan hover:scale-[1.05] transition-all cursor-pointer text-[12px] font-body text-text"
            >
              {route}
            </div>
          ))}
        </div>
      </motion.div>

      <motion.div 
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        className="flex flex-col items-center text-center mb-8"
      >
        <div 
          className="w-[88px] h-[88px] mb-4 bg-gradient-to-br from-cyan to-coral rounded-2xl flex items-center justify-center shadow-[0_0_40px_rgba(0,229,255,0.6),_0_0_80px_rgba(255,51,102,0.4)]"
          style={{ animation: 'float 4s ease-in-out infinite alternate' }}
        >
          <span className="text-[42px]">🧭</span>
        </div>
        
        <div className="font-heading font-extrabold text-[18px] bg-gradient-to-r from-cyan to-coral bg-clip-text text-transparent tracking-widest mb-3">
          NAVIGO
        </div>
        <div className="w-[60px] h-[2px] bg-gradient-to-r from-cyan to-coral mb-8"></div>
        
        <motion.h1 
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.2, duration: 0.8 }}
          className="text-4xl md:text-[56px] font-heading font-extrabold bg-gradient-to-br from-white to-cyan bg-clip-text text-transparent mb-3 leading-tight"
        >
          Where shall we wander?
        </motion.h1>
        <motion.p 
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.3, duration: 0.8 }}
          className="text-[18px] font-body text-muted italic"
        >
          Let our agents craft your perfect journey.
        </motion.p>
      </motion.div>
      
      <motion.form 
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ delay: 0.4, duration: 0.7 }}
        onSubmit={handleSubmit} 
        className="w-full max-w-[760px] group"
      >
        <div className="bg-surface backdrop-blur-2xl border-t border-cyan/20 border-b border-border border-x border-border rounded-[24px] p-8 transition-all duration-400 hover:shadow-glow-cyan">
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
      </motion.form>
      
      <motion.div 
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.6, duration: 0.8 }}
        className="mt-10 flex flex-col items-center"
      >
        <div className="flex items-center gap-2 text-muted text-[12px] uppercase tracking-wider mb-4 font-body">
          <Sparkles size={14} />
          <span>Try one of these</span>
        </div>
        <div className="flex flex-wrap justify-center gap-4">
          {chips.map((chip, idx) => (
            <motion.button
              key={idx}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.7 + idx * 0.1 }}
              onClick={() => setText(chip)}
              className="bg-surface backdrop-blur-2xl border-t border-cyan/20 border-b border-border border-x border-border rounded-full py-[8px] px-[16px] text-[14px] text-text font-body transition-all hover:border-cyan hover:scale-105 cursor-pointer"
            >
              {chip}
            </motion.button>
          ))}
        </div>
      </motion.div>

      {/* "Recently Generated" strip at bottom */}
      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 1, duration: 0.8 }}
        className="fixed bottom-4 w-full flex justify-center pointer-events-none z-50"
      >
        <div className="flex items-center gap-4 bg-surface backdrop-blur-2xl border border-cyan/10 rounded-full px-6 py-3 shadow-[0_0_20px_rgba(0,0,0,0.5)] pointer-events-auto">
          <div className="flex items-center gap-2 text-muted text-[11px] font-body uppercase tracking-wider pr-4 border-r border-border">
            <History size={12} />
            <span>Recent</span>
          </div>
          {[
            { dest: "5 days Tokyo", user: "user_a93", time: "2m ago", color: "bg-cyan" },
            { dest: "Weekend Paris", user: "user_b12", time: "15m ago", color: "bg-coral" },
            { dest: "10 days Bali", user: "user_c88", time: "1h ago", color: "bg-[#E8C547]" }
          ].map((item, i) => (
            <div key={i} className="flex items-center gap-2 px-3">
              <div className={`w-4 h-4 rounded-full ${item.color}`}></div>
              <span className="font-heading text-[12px] text-text font-semibold">{item.dest}</span>
              <span className="font-mono text-[10px] text-muted ml-1">by {item.user} &middot; {item.time}</span>
            </div>
          ))}
        </div>
      </motion.div>

    </div>
  );
};

export default TravelRequestForm;
