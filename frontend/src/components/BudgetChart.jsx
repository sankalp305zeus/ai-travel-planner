import React, { useState } from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts';

const BudgetChart = ({ breakdown }) => {
  const COLORS = ['#00E5FF', '#FF3366', '#FFFFFF', '#7A8BA6'];
  
  // Options: requested (default), USD, INR, destination
  const [currencyMode, setCurrencyMode] = useState('requested');
  
  const reqCur = breakdown.exchange_rates_used ? Object.keys(breakdown.exchange_rates_used).find(k => k.startsWith('USD_TO_'))?.split('_')[2] || 'USD' : 'USD';
  const destCur = breakdown.destination_currency_code || 'USD';
  
  const options = [
    { value: 'requested', label: `${reqCur} (Requested)` },
    { value: 'USD', label: 'USD $' },
    { value: 'INR', label: 'INR ₹' },
    { value: 'destination', label: `${destCur} (Local)` }
  ];
  // Deduplicate options if requested = INR, etc.
  const uniqueOptions = options.filter((v, i, a) => a.findIndex(t => t.label === v.label) === i);

  // Convert budget categories to selected currency using exchange rates
  // The original categories are stored in requested_currency. Let's convert back to USD then to target.
  const getRate = (mode) => {
    if (!breakdown.exchange_rates_used) return 1.0;
    const reqToUsd = breakdown.exchange_rates_used[`${reqCur}_TO_USD`] || 1.0;
    if (mode === 'requested') return 1.0;
    if (mode === 'USD') return reqToUsd;
    if (mode === 'INR') return reqToUsd * (breakdown.exchange_rates_used['USD_TO_INR'] || 83.5);
    if (mode === 'destination') return reqToUsd * (breakdown.exchange_rates_used[`USD_TO_${destCur}`] || 1.0);
    return 1.0;
  };

  const rate = getRate(currencyMode);
  
  const budgetData = (breakdown.categories || []).map(cat => ({
    ...cat,
    amount: parseFloat((cat.total * rate).toFixed(2))
  }));
  
  const totalDisplay = parseFloat(((breakdown.total_requested_currency || 0) * rate).toFixed(2));
  
  // Choose currency symbol
  const getSymbol = (mode) => {
    if (mode === 'USD') return '$';
    if (mode === 'INR') return '₹';
    if (mode === 'requested') {
       if (reqCur === 'EUR') return '€';
       if (reqCur === 'GBP') return '£';
       if (reqCur === 'INR') return '₹';
       if (reqCur === 'USD') return '$';
       if (reqCur === 'JPY') return '¥';
       return reqCur + ' ';
    }
    if (mode === 'destination') {
       if (destCur === 'EUR') return '€';
       if (destCur === 'GBP') return '£';
       if (destCur === 'INR') return '₹';
       if (destCur === 'USD') return '$';
       if (destCur === 'JPY') return '¥';
       return destCur + ' ';
    }
    return '';
  };

  return (
    <div className="flex flex-col h-full w-full">
      <div className="flex justify-end mb-2">
        <select 
          value={currencyMode}
          onChange={(e) => setCurrencyMode(e.target.value)}
          className="bg-surface border border-border-strong text-text text-sm rounded-lg p-1.5 outline-none font-mono hover:shadow-glow-cyan transition-shadow"
        >
          {uniqueOptions.map(opt => (
            <option key={opt.value} value={opt.value}>{opt.label}</option>
          ))}
        </select>
      </div>
      <div className="h-40 w-full relative">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={budgetData}
              cx="50%"
              cy="50%"
              innerRadius={45}
              outerRadius={60}
              paddingAngle={5}
              dataKey="amount"
              nameKey="category"
              stroke="none"
            >
              {budgetData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
              ))}
            </Pie>
            <Tooltip 
              formatter={(value) => `${getSymbol(currencyMode)}${value}`}
              contentStyle={{ backgroundColor: 'rgba(14,23,41,0.8)', borderColor: 'rgba(0,229,255,0.4)', color: '#E8F0FF', borderRadius: '8px' }}
              itemStyle={{ color: '#E8F0FF' }}
            />
          </PieChart>
        </ResponsiveContainer>
      </div>
      <div className="mt-4 flex flex-col gap-2">
        {budgetData.map((entry, index) => (
          <div key={index} className="flex items-center justify-between font-body text-[13px] text-text">
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: COLORS[index % COLORS.length] }}></span>
              <span className="capitalize">{entry.category.replace('_', ' ')}</span>
            </div>
            <span className="font-mono text-muted">{getSymbol(currencyMode)}{entry.amount}</span>
          </div>
        ))}
      </div>
    </div>
  );
};

export default BudgetChart;
