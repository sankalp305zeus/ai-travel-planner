import React, { useState } from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts';

const BudgetChart = ({ breakdown }) => {
  const COLORS = ['#E8C547', '#4ECDC4', '#F0EDE8', '#888580'];
  
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
          className="bg-bg border border-border text-text-primary text-sm rounded p-1 outline-none font-mono"
        >
          {uniqueOptions.map(opt => (
            <option key={opt.value} value={opt.value}>{opt.label}</option>
          ))}
        </select>
      </div>
      <div className="h-56 w-full relative">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={budgetData}
              cx="50%"
              cy="50%"
              innerRadius={50}
              outerRadius={70}
              paddingAngle={5}
              dataKey="amount"
              nameKey="category"
            >
              {budgetData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
              ))}
            </Pie>
            <Tooltip 
              formatter={(value) => `${getSymbol(currencyMode)}${value}`}
              contentStyle={{ backgroundColor: '#1A1A1A', borderColor: '#2A2A2A', color: '#F0EDE8' }}
              itemStyle={{ color: '#F0EDE8' }}
            />
          </PieChart>
        </ResponsiveContainer>
      </div>
      <div className="mt-4 text-center font-mono text-lg text-text-primary">
        Total: {getSymbol(currencyMode)}{totalDisplay}
      </div>
    </div>
  );
};

export default BudgetChart;
