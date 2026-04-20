'use client';

import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";
import type { WellHistory } from "@/types";

export function WellHistoryChart({ data }: { data: WellHistory }) {
  const chartData = data.timestamps.map((t, i) => ({
    date: t.slice(5, 10), // MM-DD
    value: data.values[i],
  }));
  // Sample every Nth point to avoid overcrowding
  const step = Math.max(1, Math.floor(chartData.length / 60));
  const sampled = chartData.filter((_, i) => i % step === 0);

  return (
    <div className="mt-2 bg-white rounded border p-2">
      <div className="text-xs font-medium mb-1">
        {data.well_id}: {data.parameter} (trend: {data.trend})
      </div>
      <ResponsiveContainer width="100%" height={120}>
        <LineChart data={sampled}>
          <XAxis dataKey="date" tick={{ fontSize: 9 }} interval="preserveStartEnd" />
          <YAxis tick={{ fontSize: 9 }} width={40} />
          <Tooltip contentStyle={{ fontSize: 11 }} />
          <Line type="monotone" dataKey="value" stroke="#3b82f6" strokeWidth={1.5} dot={false} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
