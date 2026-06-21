import React, { useState, useEffect } from 'react';
import ShinyText from './ui/shiny-text';

const placeholders = [
  "5 days Japan, ₹3,00,000 budget, food and temples, hate crowds",
  "Weekend Paris, ₹80,000, art museums, no queues",
  "2 weeks Southeast Asia, $2000, beaches and food"
];

const TravelRequestForm = ({ onSubmit }) => {
  const [text, setText] = useState('');
  const [placeholderIdx, setPlaceholderIdx] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setPlaceholderIdx((prev) => (prev + 1) % placeholders.length);
    }, 3000);
    return () => clearInterval(interval);
  }, []);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (text.length > 0 && text.length <= 500) {
      onSubmit(text);
    }
  };

  return (
    <div className="relative z-10 flex flex-col items-center justify-center min-h-screen w-full px-4">
      <div className="mb-12 text-center">
        <h1 className="text-4xl md:text-6xl font-heading text-text-primary mb-4">
          <ShinyText text="Where do you want to go?" />
        </h1>
      </div>
      
      <form onSubmit={handleSubmit} className="w-full max-w-2xl bg-surface/90 backdrop-blur border border-border p-6 rounded-2xl shadow-2xl">
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder={placeholders[placeholderIdx]}
          className="w-full h-40 bg-transparent text-text-primary placeholder-text-muted text-lg outline-none resize-none font-body"
          maxLength={500}
        />
        
        <div className="flex justify-between items-center mt-4 border-t border-border pt-4">
          <span className="font-mono text-sm text-text-muted">
            {text.length}/500
          </span>
          <button
            type="submit"
            disabled={text.length === 0 || text.length > 500}
            className="bg-accent-amber text-bg font-body font-semibold py-3 px-8 rounded-full transition-transform hover:scale-105 disabled:opacity-50 disabled:hover:scale-100"
          >
            Plan My Trip &rarr;
          </button>
        </div>
      </form>
    </div>
  );
};

export default TravelRequestForm;
