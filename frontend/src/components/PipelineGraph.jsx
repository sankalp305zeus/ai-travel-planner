import React from 'react';
import AgentNode from './AgentNode';

const PipelineGraph = ({ agents }) => {
  return (
    <div className="flex flex-col items-center gap-12 p-8">
      {/* Row 1 */}
      <div className="flex justify-center">
        <AgentNode name="Orchestrator" {...agents.Orchestrator} />
      </div>
      
      {/* Row 2 */}
      <div className="flex justify-center gap-16">
        <AgentNode name="Destination" {...agents.Destination} />
        <AgentNode name="Logistics" {...agents.Logistics} />
        <AgentNode name="Budget" {...agents.Budget} />
      </div>
      
      {/* Row 3 */}
      <div className="flex justify-center">
        <AgentNode name="Review" {...agents.Review} />
      </div>
    </div>
  );
};

export default PipelineGraph;
