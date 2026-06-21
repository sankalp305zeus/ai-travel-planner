import React from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts';

const BudgetChart = ({ budgetData }) => {
  const COLORS = ['#E8C547', '#4ECDC4', '#F0EDE8', '#888580'];

  return (
    <div className="h-64 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie
            data={budgetData}
            cx="50%"
            cy="50%"
            innerRadius={60}
            outerRadius={80}
            paddingAngle={5}
            dataKey="amount"
            nameKey="category"
          >
            {budgetData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
            ))}
          </Pie>
          <Tooltip 
            contentStyle={{ backgroundColor: '#1A1A1A', borderColor: '#2A2A2A', color: '#F0EDE8' }}
            itemStyle={{ color: '#F0EDE8' }}
          />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
};

export default BudgetChart;
