import React from 'react';

const AgentNode = ({ name, state, artifact }) => {
  const stateStyles = {
    waiting: 'border-muted text-muted',
    active: 'border-accent-amber text-accent-amber animate-pulse shadow-[0_0_15px_#E8C547]',
    complete: 'bg-accent-teal border-accent-teal text-bg',
    error: 'bg-accent-red border-accent-red text-text-primary'
  };

  const baseStyle = "w-32 h-32 rounded-full flex items-center justify-center border-2 font-body text-sm font-medium text-center transition-all duration-300";

  return (
    <div className="flex flex-col items-center">
      <div className={`${baseStyle} ${stateStyles[state]}`}>
        {name}
      </div>
    </div>
  );
};

export default AgentNode;
