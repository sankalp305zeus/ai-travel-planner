import React, { useState, useEffect } from 'react';

const PLACEHOLDERS = [
  "Plan a 5-day trip to Japan. Tokyo + Kyoto. $3,000 budget. Love food and temples, hate crowds.",
  "7 days in Italy. Rome and Florence. €2,000 budget. Art museums, historical sites, family-friendly.",
  "Weekend in Paris. €500. Art museums, cozy cafes, no queues."
];

export default function App() {
  const [placeholderIndex, setPlaceholderIndex] = useState(0);
  const [request, setRequest] = useState("");

  useEffect(() => {
    const interval = setInterval(() => {
      setPlaceholderIndex((prev) => (prev + 1) % PLACEHOLDERS.length);
    }, 4000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="min-h-screen bg-bg text-text font-sans flex flex-col justify-between p-6 md:p-12 selection:bg-accent/30 selection:text-accent">
      <header className="w-full max-w-4xl mx-auto flex justify-between items-center py-4">
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-accent animate-pulse" />
          <span className="font-mono text-sm tracking-wider uppercase text-muted">AI Travel Planner</span>
        </div>
        <span className="font-mono text-xs text-muted border border-border px-2 py-1 rounded">v0.1-dev</span>
      </header>

      <main className="flex-grow flex items-center justify-center py-12">
        <div className="w-full max-w-2xl flex flex-col gap-8">
          <div className="space-y-3">
            <h1 className="font-display text-4xl md:text-5xl font-normal text-text tracking-tight">
              Where to next?
            </h1>
            <p className="text-muted text-sm md:text-base font-light">
              Enter your destination, duration, budget, preferences, and avoidances to generate a verified itinerary.
            </p>
          </div>

          <div className="relative border border-border bg-surface rounded-xl p-4 focus-within:border-accent/50 transition-all duration-300 shadow-xl shadow-black/40">
            <textarea
              value={request}
              onChange={(e) => setRequest(e.target.value)}
              className="w-full h-32 bg-transparent text-text border-none resize-none focus:outline-none focus:ring-0 placeholder-muted/50 text-base font-light leading-relaxed"
              placeholder={PLACEHOLDERS[placeholderIndex]}
              maxLength={500}
            />
            <div className="flex justify-between items-center mt-4 pt-4 border-t border-border/50">
              <span className="text-xs font-mono text-muted">{request.length}/500</span>
              <button
                type="button"
                className="bg-accent hover:bg-accent/90 text-bg px-6 py-2.5 rounded-lg text-sm font-semibold tracking-wide flex items-center gap-2 transition-all active:scale-[0.98]"
              >
                Plan My Trip
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M14 5l7 7m0 0l-7 7m7-7H3" />
                </svg>
              </button>
            </div>
          </div>
        </div>
      </main>

      <footer className="w-full max-w-4xl mx-auto py-4 border-t border-border/30 flex flex-col sm:flex-row justify-between items-center gap-4 text-xs font-mono text-muted">
        <div>
          <span>Travel information from Wikivoyage, CC BY-SA 3.0</span>
          <span className="mx-2">•</span>
          <span>Map data © OpenStreetMap contributors</span>
        </div>
        <div>
          <span>Precision Intelligence Engine</span>
        </div>
      </footer>
    </div>
  );
}
