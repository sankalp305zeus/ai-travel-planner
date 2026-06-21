import React from 'react';

const ActivityCard = ({ name, duration, crowd_level, cost_band, rationale }) => {
  const crowdColors = {
    low: 'bg-accent-teal text-bg',
    medium: 'bg-accent-amber text-bg',
    high: 'bg-accent-red text-text-primary'
  };

  return (
    <div className="bg-surface border border-border p-4 rounded-lg mb-4 font-body">
      <div className="flex justify-between items-start mb-2">
        <h4 className="text-lg font-heading text-text-primary">{name}</h4>
        <span className={`px-2 py-1 text-xs font-semibold rounded ${crowdColors[crowd_level] || crowdColors.medium}`}>
          Crowd: {crowd_level}
        </span>
      </div>
      <p className="text-text-muted text-sm mb-2">{duration} hrs • Cost: {cost_band}</p>
      <p className="text-text-primary text-sm">{rationale}</p>
    </div>
  );
};

export default ActivityCard;
