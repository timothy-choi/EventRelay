"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { TooltipProps } from "recharts";

import { EndpointStats, SystemStats } from "../lib/types";

type StatusDatum = {
  name: string;
  value: number;
  fill: string;
};

type LatencyDatum = {
  name: string;
  latency_ms: number;
};

type DeliveryTrendDatum = {
  minute: string;
  count: number;
};

type EndpointReliabilityDatum = {
  name: string;
  success_rate: number;
};

type DashboardChartsProps = {
  endpointStats: EndpointStats[];
  statusCounts: {
    succeeded: number;
    failed: number;
    retrying: number;
  };
  systemStats: SystemStats | null;
  deliveriesOverTime: DeliveryTrendDatum[];
};

const statusColors = {
  succeeded: "#0e7c66",
  failed: "#b94a2f",
  retrying: "#d28a33",
};

function formatMetric(value: number | null): string {
  if (value === null) {
    return "n/a";
  }
  return `${Math.round(value)} ms`;
}

function formatTooltipValue(value: string | number): string {
  return `${Math.round(Number(value))} ms`;
}

function formatPercentValue(value: string | number): string {
  return `${value}%`;
}

export default function DashboardCharts({
  endpointStats,
  statusCounts,
  systemStats,
  deliveriesOverTime,
}: DashboardChartsProps) {
  const statusData: StatusDatum[] = [
    { name: "Succeeded", value: statusCounts.succeeded, fill: statusColors.succeeded },
    { name: "Failed", value: statusCounts.failed, fill: statusColors.failed },
    { name: "Retrying", value: statusCounts.retrying, fill: statusColors.retrying },
  ];

  const latencyData: LatencyDatum[] = [
    { name: "Average", latency_ms: systemStats?.avg_latency_ms ?? 0 },
    { name: "P95", latency_ms: systemStats?.p95_latency_ms ?? 0 },
  ];

  const endpointReliabilityData: EndpointReliabilityDatum[] = endpointStats
    .filter((stats) => stats.total_deliveries > 0)
    .sort((left, right) => right.success_rate - left.success_rate)
    .slice(0, 6)
    .map((stats) => ({
      name: stats.endpoint_name,
      success_rate: Number(stats.success_rate.toFixed(1)),
    }));

  return (
    <div className="grid two">
      <div className="card">
        <div className="page-header chart-header">
          <h2 className="section-title">Success vs failure</h2>
          <p>How recent deliveries are resolving across the system.</p>
        </div>
        <div className="chart-shell">
          <ResponsiveContainer width="100%" height={260}>
            <PieChart>
              <Pie
                data={statusData}
                dataKey="value"
                nameKey="name"
                cx="50%"
                cy="50%"
                outerRadius={84}
                innerRadius={44}
                paddingAngle={3}
              >
                {statusData.map((entry) => (
                  <Cell key={entry.name} fill={entry.fill} />
                ))}
              </Pie>
              <Tooltip />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="card">
        <div className="page-header chart-header">
          <h2 className="section-title">Latency</h2>
          <p>Overall system latency from recorded delivery attempts.</p>
        </div>
        <div className="grid stats compact-stats">
          <div>
            <div className="muted">Avg latency</div>
            <div className="metric compact">{formatMetric(systemStats?.avg_latency_ms ?? null)}</div>
          </div>
          <div>
            <div className="muted">P95 latency</div>
            <div className="metric compact">{formatMetric(systemStats?.p95_latency_ms ?? null)}</div>
          </div>
        </div>
        <div className="chart-shell">
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={latencyData}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip formatter={formatTooltipValue as TooltipProps<string | number, string>["formatter"]} />
              <Bar dataKey="latency_ms" fill="#0e7c66" radius={[8, 8, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="card">
        <div className="page-header chart-header">
          <h2 className="section-title">Deliveries over time</h2>
          <p>Delivery volume per minute for the most recent activity window.</p>
        </div>
        <div className="chart-shell">
          <ResponsiveContainer width="100%" height={260}>
            <LineChart data={deliveriesOverTime}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} />
              <XAxis dataKey="minute" />
              <YAxis allowDecimals={false} />
              <Tooltip />
              <Line
                type="monotone"
                dataKey="count"
                stroke="#0e7c66"
                strokeWidth={3}
                dot={{ r: 3 }}
                activeDot={{ r: 5 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="card">
        <div className="page-header chart-header">
          <h2 className="section-title">Endpoint reliability</h2>
          <p>Success rate highlights reliability differences between active targets.</p>
        </div>
        {endpointReliabilityData.length > 0 ? (
          <div className="chart-shell">
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={endpointReliabilityData} layout="vertical" margin={{ left: 12, right: 12 }}>
                <CartesianGrid strokeDasharray="3 3" horizontal={false} />
                <XAxis type="number" domain={[0, 100]} unit="%" />
                <YAxis type="category" dataKey="name" width={110} />
                <Tooltip formatter={formatPercentValue as TooltipProps<string | number, string>["formatter"]} />
                <Bar dataKey="success_rate" fill="#0e7c66" radius={[0, 8, 8, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        ) : (
          <p className="muted">Endpoint reliability charts will appear after deliveries have been recorded.</p>
        )}
      </div>
    </div>
  );
}
