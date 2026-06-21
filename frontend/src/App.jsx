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
      {view === 'request' && <Aurora />}
      {view === 'generating' && <SplashCursor />}
      
      {view === 'request' && (
        <TravelRequestForm onSubmit={handleSubmit} />
      )}
      
      {view === 'generating' && (
        <div className="flex w-full min-h-screen">
          <div className="flex-1 flex flex-col items-center justify-center p-8">
            <h2 className="text-3xl font-heading text-text-primary mb-12">Building your itinerary...</h2>
            <PipelineGraph agents={agentStatus} />
          </div>
          <div className="w-96 bg-surface border-l border-border p-6 flex flex-col">
            <h3 className="text-xl font-heading text-accent-teal mb-6">Agent Outputs</h3>
            <div className="space-y-4 font-mono text-sm text-text-muted flex-1 overflow-y-auto">
              {Object.entries(agentStatus).map(([name, data]) => (
                <div key={name}>
                  <strong className="text-text-primary">{name}:</strong> {data.artifact || '...'}
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {view === 'itinerary' && itinerary && (
        <div className="pb-24">
          <div className="max-w-6xl mx-auto p-8 flex gap-8">
            <div className="flex-1">
              <h1 className="text-4xl font-heading text-text-primary mb-8">Your Itinerary</h1>
              
              <div className="flex gap-4 mb-8 overflow-x-auto pb-2 border-b border-border">
                {itinerary.day_skeletons && itinerary.day_skeletons.map((day, idx) => (
                  <button
                    key={day.day_number}
                    onClick={() => setActiveDayIndex(idx)}
                    className={`pb-2 px-2 font-heading whitespace-nowrap transition-colors ${activeDayIndex === idx ? 'text-accent-amber border-b-2 border-accent-amber' : 'text-[#888580] hover:text-text-primary'}`}
                  >
                    Day {day.day_number}
                  </button>
                ))}
              </div>
              
              {itinerary.day_skeletons && itinerary.day_skeletons[activeDayIndex] && (() => {
                const day = itinerary.day_skeletons[activeDayIndex];
                return (
                  <div key={day.day_number} className="mb-12 transition-opacity duration-200 opacity-100">
                    <h2 className="text-2xl font-heading text-accent-amber mb-6 border-b border-border pb-2">
                      <BlurText text={`Day ${day.day_number} — ${day.city}`} />
                    </h2>
                    <div className="text-text-muted mb-4 text-sm">Hotel: {day.lodging_hotel_name}</div>
                    
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
                      <div className="bg-surface border border-border rounded-lg p-6 my-4 text-[#888580] italic">
                        Explore on your own — wander the local neighborhoods
                      </div>
                    )}
                  </div>
                );
              })()}
            </div>
            
            <div className="w-80">
              <div className="sticky top-8">
                <h3 className="text-xl font-heading text-text-primary mb-4">Budget Breakdown</h3>
                <div className="bg-surface border border-border rounded-lg p-4">
                  {itinerary.budget_breakdown && (
                    <BudgetChart breakdown={itinerary.budget_breakdown} />
                  )}
                </div>
              </div>
            </div>
          </div>
          
          <div className="fixed bottom-0 w-full bg-accent-amber text-bg py-3 px-6 text-center font-medium shadow-lg z-50">
            AI-generated estimates. Confirm all prices, availability, and bookings independently.
          </div>
          <div className="text-center text-text-muted text-xs mt-8 mb-4">
            Data attribution: OpenStreetMap & Wikivoyage (CC BY-SA 3.0)
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
