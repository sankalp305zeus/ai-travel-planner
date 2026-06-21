import React from 'react';
import AgentNode from './AgentNode';

const PipelineGraph = ({ agents }) => {
  // Check if a line should be active
  // Active if the target agent is active or complete
  const isActive = (agentName) => ['active', 'complete'].includes(agents[agentName]?.state);

  return (
    <div className="relative flex flex-col items-center gap-12 p-8 min-w-[800px]">
      {/* SVG Flow Lines */}
      <svg className="absolute inset-0 w-full h-full" style={{ zIndex: 0 }}>
        {/* Orchestrator to Destination */}
        <path
          d="M 400 120 C 400 180, 200 220, 200 240"
          fill="none"
          strokeWidth="2"
          strokeDasharray="6 6"
          className={isActive('Destination') ? 'stroke-cyan flow-path-active' : 'stroke-[rgba(122,139,166,0.2)]'}
        />
        {/* Orchestrator to Logistics */}
        <path
          d="M 400 120 C 400 180, 400 220, 400 240"
          fill="none"
          strokeWidth="2"
          strokeDasharray="6 6"
          className={isActive('Logistics') ? 'stroke-cyan flow-path-active' : 'stroke-[rgba(122,139,166,0.2)]'}
        />
        {/* Orchestrator to Budget */}
        <path
          d="M 400 120 C 400 180, 600 220, 600 240"
          fill="none"
          strokeWidth="2"
          strokeDasharray="6 6"
          className={isActive('Budget') ? 'stroke-cyan flow-path-active' : 'stroke-[rgba(122,139,166,0.2)]'}
        />

        {/* Destination to Review */}
        <path
          d="M 200 380 C 200 440, 400 460, 400 500"
          fill="none"
          strokeWidth="2"
          strokeDasharray="6 6"
          className={isActive('Review') ? 'stroke-cyan flow-path-active' : 'stroke-[rgba(122,139,166,0.2)]'}
        />
        {/* Logistics to Review */}
        <path
          d="M 400 380 C 400 440, 400 460, 400 500"
          fill="none"
          strokeWidth="2"
          strokeDasharray="6 6"
          className={isActive('Review') ? 'stroke-cyan flow-path-active' : 'stroke-[rgba(122,139,166,0.2)]'}
        />
        {/* Budget to Review */}
        <path
          d="M 600 380 C 600 440, 400 460, 400 500"
          fill="none"
          strokeWidth="2"
          strokeDasharray="6 6"
          className={isActive('Review') ? 'stroke-cyan flow-path-active' : 'stroke-[rgba(122,139,166,0.2)]'}
        />
      </svg>

      {/* Row 1 */}
      <div className="flex justify-center w-full">
        <AgentNode name="Orchestrator" {...agents.Orchestrator} />
      </div>
      
      {/* Row 2 */}
      <div className="flex justify-center gap-16 w-full">
        <AgentNode name="Destination" {...agents.Destination} />
        <AgentNode name="Logistics" {...agents.Logistics} />
        <AgentNode name="Budget" {...agents.Budget} />
      </div>
      
      {/* Row 3 */}
      <div className="flex justify-center w-full">
        <AgentNode name="Review" {...agents.Review} />
      </div>
    </div>
  );
};

export default PipelineGraph;
