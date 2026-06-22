import React, { useState, useEffect } from 'react';
import Aurora from './components/ui/aurora';
import SplashCursor from './components/ui/splash-cursor';
import BlurText from './components/ui/blur-text';
import TravelRequestForm from './components/TravelRequestForm';
import PipelineGraph from './components/PipelineGraph';
import ActivityCard from './components/ActivityCard';
import BudgetChart from './components/BudgetChart';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

function App() {
  const [view, setView] = useState('request'); // 'request' | 'generating' | 'itinerary'
  const [planId, setPlanId] = useState(null);
  
  const [agentStatus, setAgentStatus] = useState({
    Orchestrator: { state: 'waiting', artifact: null },
    Destination: { state: 'waiting', artifact: null },
    Logistics: { state: 'waiting', artifact: null },
    Budget: { state: 'waiting', artifact: null },
    Review: { state: 'waiting', artifact: null }
  });
  
  const [itinerary, setItinerary] = useState(null);
  const [activeDayIndex, setActiveDayIndex] = useState(0);

  const fetchItinerary = async (id) => {
    try {
      const res = await fetch(`${API_URL}/api/plan/${id}`);
      const data = await res.json();
      setItinerary(data);
      setView('itinerary');
    } catch (err) {
      console.error(err);
    }
  };

  const handleSubmit = async (text) => {
    setView('generating');
    
    setAgentStatus({
      Orchestrator: { state: 'waiting', artifact: null },
      Destination: { state: 'waiting', artifact: null },
      Logistics: { state: 'waiting', artifact: null },
      Budget: { state: 'waiting', artifact: null },
      Review: { state: 'waiting', artifact: null }
    });

    try {
      const response = await fetch(`${API_URL}/api/plan`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ request: text })
      });
      
      const data = await response.json();
      const newPlanId = data.plan_id;
      setPlanId(newPlanId);
      
      const es = new EventSource(`${API_URL}/api/plan/${newPlanId}/stream`);
      es.onmessage = (e) => {
        const payload = JSON.parse(e.data);
        if (payload.agent) {
          setAgentStatus(prev => ({
            ...prev,
            [payload.agent]: { state: payload.state, artifact: payload.artifact }
          }));
        }
        if (payload.status === 'completed') {
          es.close();
          fetchItinerary(newPlanId);
        }
        if (payload.status === 'error') {
          es.close();
          setAgentStatus(prev => ({
            ...prev,
            Orchestrator: { state: 'error', artifact: 'Planning failed' }
          }));
        }
      };
      
    } catch (err) {
      console.error(err);
      setAgentStatus(prev => ({
        ...prev,
        Orchestrator: { state: 'error', artifact: null }
      }));
    }
  };

  return (
    <div className="relative min-h-screen w-full font-body overflow-x-hidden">
      {/* Liquid Background */}
      <div className="liquid-bg">
        <div className="liquid-blob-1"></div>
        <div className="liquid-blob-2"></div>
        <div className="liquid-blob-3"></div>
      </div>
      
      {/* Global Branding */}
      {view !== 'request' && (
        <div className="absolute top-6 left-8 z-50 animate-in fade-in slide-in-from-top-4 duration-500">
          <div className="font-heading font-extrabold text-[24px] bg-gradient-to-r from-cyan to-coral bg-clip-text text-transparent tracking-tight">
            NAVIGO
          </div>
          <div className="flex items-center gap-2 mt-[2px]">
            <div className="w-6 h-px bg-cyan"></div>
            <div className="font-body text-[11px] text-muted lowercase tracking-[0.15em]">
              ai travel intelligence
            </div>
          </div>
        </div>
      )}
      
      {view === 'request' && (
        <TravelRequestForm onSubmit={handleSubmit} />
      )}
      
      {view === 'generating' && (
        <div className="flex w-full min-h-screen animate-in fade-in slide-in-from-bottom-2 duration-400">
          <div className="flex-1 flex flex-col items-center justify-center p-8">
            <h2 className="text-[42px] font-heading font-extrabold bg-gradient-to-br from-white to-cyan bg-clip-text text-transparent mb-2 drop-shadow-lg">
              Crafting your journey...
            </h2>
            <p className="text-[16px] text-muted font-body mb-10">
              Five specialized agents are working in parallel
            </p>
            <div className="bg-surface backdrop-blur-2xl border-t border-cyan/20 border-b border-border border-x border-border rounded-[28px] p-[60px] shadow-[0_0_40px_rgba(0,229,255,0.1)] relative">
               <PipelineGraph agents={agentStatus} />
            </div>
          </div>
          <div className="w-[340px] bg-surface backdrop-blur-2xl border-l border-cyan/20 fixed right-0 h-full p-6 flex flex-col z-20 shadow-[-10px_0_30px_rgba(0,0,0,0.5)]">
            <div className="flex items-center gap-3 mb-8">
              <h3 className="text-[18px] font-heading text-text font-bold">Live Updates</h3>
              <div className="w-2 h-2 rounded-full bg-cyan animate-pulse shadow-glow-cyan"></div>
            </div>
            <div className="space-y-5 flex-1 overflow-y-auto pr-2 custom-scrollbar">
              {Object.entries(agentStatus).map(([name, data]) => (
                <div key={name} className="animate-in fade-in slide-in-from-right-4 duration-500 border-l-[2px] border-transparent transition-colors">
                  <div className="text-coral font-heading text-[14px] font-semibold uppercase tracking-wider mb-1">{name}</div>
                  <div className="font-mono text-[12px] text-muted leading-[1.5]">{data.artifact || 'Awaiting signal...'}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {view === 'itinerary' && itinerary && (
        <div className="pb-24 animate-in fade-in slide-in-from-bottom-4 duration-400">
          <div className="max-w-[1200px] mx-auto p-8 flex gap-10 pt-32">
            <div className="flex-1">
              
              <div className="mb-10">
                <div className="bg-surface backdrop-blur-2xl w-full py-10 rounded-[24px] border-t border-cyan/20 border-b border-border border-x border-border relative overflow-hidden flex items-center justify-between px-12 shadow-[0_0_40px_rgba(0,229,255,0.1)] transition-transform hover:scale-[1.01] duration-500">
                  {/* Subtle gradient mesh overlay */}
                  <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top_left,_rgba(0,229,255,0.15),_transparent_50%),radial-gradient(ellipse_at_bottom_right,_rgba(255,51,102,0.1),_transparent_50%)]"></div>
                  
                  <div className="relative z-10">
                    <h1 className="text-[56px] font-heading font-extrabold bg-gradient-to-br from-white to-cyan bg-clip-text text-transparent leading-tight drop-shadow-lg">
                      {itinerary?.constraints?.duration_days || 5} Days in {itinerary?.constraints?.cities?.[0] || 'Destination'}
                    </h1>
                  </div>
                  <div className="relative z-10 text-right">
                    <div className="text-[12px] uppercase tracking-wider text-muted font-body font-semibold mb-1">Total Budget</div>
                    <div className="text-[36px] font-body text-coral font-bold drop-shadow-[0_0_15px_rgba(255,51,102,0.3)]">
                      {itinerary?.constraints?.requested_currency === 'INR' ? '₹' : (itinerary?.constraints?.requested_currency === 'USD' ? '$' : '')}
                      {itinerary?.constraints?.budget_total?.toLocaleString() || '---'}
                    </div>
                  </div>
                </div>
              </div>
              
              <div className="flex gap-2 mb-8 overflow-x-auto pb-0 border-b border-[rgba(122,139,166,0.2)] sticky top-0 bg-canvas/80 backdrop-blur z-30 pt-4">
                {itinerary.day_skeletons && itinerary.day_skeletons.map((day, idx) => (
                  <button
                    key={day.day_number}
                    onClick={() => setActiveDayIndex(idx)}
                    className={`relative pb-3 px-4 font-body text-[15px] whitespace-nowrap transition-colors duration-300 ${activeDayIndex === idx ? 'text-cyan font-medium' : 'text-muted hover:text-text'}`}
                  >
                    Day {day.day_number}
                    {activeDayIndex === idx && (
                      <div className="absolute bottom-0 left-0 w-full h-[2px] bg-gradient-to-r from-cyan to-coral animate-in fade-in zoom-in duration-300"></div>
                    )}
                  </button>
                ))}
              </div>
              
              {itinerary.day_skeletons && itinerary.day_skeletons[activeDayIndex] && (() => {
                const day = itinerary.day_skeletons[activeDayIndex];
                return (
                  <div key={day.day_number} className="mb-12 animate-in fade-in slide-in-from-bottom-4 duration-400">
                    <h2 className="text-[28px] font-heading font-bold text-text mb-2">
                      {day.city}
                    </h2>
                    <div className="text-muted mb-8 text-[14px] flex items-center gap-2">
                      <div className="w-1.5 h-1.5 rounded-full bg-cyan opacity-50"></div>
                      Lodging: <span className="text-text">{day.lodging_hotel_name}</span>
                    </div>
                    
                    {day.activities && day.activities.length > 0 ? (
                      day.activities.map((act, i) => (
                        <ActivityCard 
                          key={i}
                          name={act.name}
                          duration={act.duration_hours}
                          crowd_level={itinerary.activity_catalog?.activities?.find(a => a.id === act.activity_id)?.crowd_level || 'medium'}
                          cost_band={itinerary.activity_catalog?.activities?.find(a => a.id === act.activity_id)?.cost_band || 'medium'}
                          rationale={act.rationale}
                        />
                      ))
                    ) : (
                      <div className="bg-surface backdrop-blur-md border border-[rgba(122,139,166,0.2)] rounded-[18px] p-8 text-center text-muted italic font-body">
                        Explore on your own — wander the local neighborhoods
                      </div>
                    )}
                  </div>
                );
              })()}
            </div>
            
            <div className="w-[320px]">
              <div className="sticky top-32">
                <div className="text-[12px] uppercase tracking-wider text-muted font-body font-semibold mb-2">Estimated Cost</div>
                <div className="text-[36px] font-heading text-cyan font-bold mb-6">
                  {itinerary?.constraints?.requested_currency === 'INR' ? '₹' : (itinerary?.constraints?.requested_currency === 'USD' ? '$' : '')}
                  {itinerary.budget_breakdown?.total_requested_currency?.toLocaleString() || '---'}
                </div>
                <div className="bg-surface backdrop-blur-md border border-border-strong rounded-[24px] p-6 shadow-glow-cyan/20">
                  {itinerary.budget_breakdown && (
                    <BudgetChart breakdown={itinerary.budget_breakdown} />
                  )}
                </div>
              </div>
            </div>
          </div>
          
          <div className="text-center text-muted text-[11px] mb-2 font-body">
            Data: Wikivoyage CC BY-SA 3.0 &middot; OpenStreetMap
          </div>
          <div className="fixed bottom-0 w-full h-[40px] bg-surface backdrop-blur-xl border-t border-border flex items-center justify-center z-50">
            <div className="absolute top-0 left-0 w-full h-[1px] bg-gradient-to-r from-cyan to-coral opacity-50"></div>
            <span className="text-[13px] font-body text-muted">AI-generated estimates. Verify all bookings independently.</span>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
