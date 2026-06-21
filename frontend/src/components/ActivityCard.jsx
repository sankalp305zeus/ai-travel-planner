import React from 'react';

const ActivityCard = ({ name, duration, crowd_level, cost_band, rationale }) => {
  const borderColors = {
    low: 'border-l-cyan',
    medium: 'border-l-coral',
    high: 'border-l-[#FF3366]'
  };

  const badgeColors = {
    low: 'text-cyan bg-[rgba(0,229,255,0.1)]',
    medium: 'text-coral bg-[rgba(255,51,102,0.1)]',
    high: 'text-[#FF3366] bg-[rgba(255,51,102,0.1)]'
  };

  return (
    <div className={`bg-surface backdrop-blur-md rounded-[18px] p-6 mb-5 font-body border border-border-strong border-l-[4px] ${borderColors[crowd_level] || borderColors.medium} transition-all duration-300 hover:-translate-y-1 hover:shadow-glow-cyan`}>
      <div className="flex justify-between items-start mb-3">
        <h4 className="text-[20px] font-heading font-semibold text-text">{name}</h4>
        <span className={`px-2 py-1 text-[11px] font-bold uppercase tracking-wider rounded-md ${badgeColors[crowd_level] || badgeColors.medium}`}>
          Crowd: {crowd_level}
        </span>
      </div>
      <p className="font-mono text-[12px] text-muted mb-3 tracking-wide">
        {duration} hrs &bull; Cost: {cost_band}
      </p>
      <p className="text-[14px] text-text leading-[1.6]">
        {rationale}
      </p>
    </div>
  );
};

export default ActivityCard;
