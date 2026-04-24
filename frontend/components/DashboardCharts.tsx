"use client";

import { EndpointStats, SystemStats } from "../lib/types";

type DeliveryTrendDatum = {
  minute: string;
  count: number;
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

type DonutSegment = {
  label: string;
  value: number;
  color: string;
};

type ReliabilityDatum = {
  name: string;
  success_rate: number;
};

const successColor = "#0e7c66";
const failureColor = "#b94a2f";
const retryingColor = "#d28a33";
const trackColor = "#ede5d8";

function formatMetric(value: number | null): string {
  if (value === null) {
    return "n/a";
  }
  return `${Math.round(value)} ms`;
}

function renderDonutSegments(segments: DonutSegment[], radius: number, strokeWidth: number) {
  const total = Math.max(segments.reduce((sum, segment) => sum + segment.value, 0), 1);
  const circumference = 2 * Math.PI * radius;
  let offset = 0;

  return segments.map((segment) => {
    const length = (segment.value / total) * circumference;
    const circle = (
      <circle
        key={segment.label}
        cx="60"
        cy="60"
        r={radius}
        fill="none"
        stroke={segment.color}
        strokeWidth={strokeWidth}
        strokeDasharray={`${length} ${circumference - length}`}
        strokeDashoffset={-offset}
        strokeLinecap="round"
      />
    );
    offset += length;
    return circle;
  });
}

function SimpleDonutChart({ segments }: { segments: DonutSegment[] }) {
  const total = segments.reduce((sum, segment) => sum + segment.value, 0);

  return (
    <div className="simple-chart split-chart">
      <div className="donut-wrap">
        <svg viewBox="0 0 120 120" className="donut-chart" aria-label="Delivery status chart">
          <circle cx="60" cy="60" r="38" fill="none" stroke={trackColor} strokeWidth="18" />
          {renderDonutSegments(segments, 38, 18)}
        </svg>
        <div className="donut-center">
          <strong>{total}</strong>
          <span>Total</span>
        </div>
      </div>
      <div className="legend-list">
        {segments.map((segment) => (
          <div key={segment.label} className="legend-item">
            <span className="legend-swatch" style={{ backgroundColor: segment.color }} />
            <span>{segment.label}</span>
            <strong>{segment.value}</strong>
          </div>
        ))}
      </div>
    </div>
  );
}

function MetricBarChart({
  data,
}: {
  data: Array<{ label: string; value: number | null; color: string }>;
}) {
  const maxValue = Math.max(...data.map((item) => item.value ?? 0), 1);

  return (
    <div className="simple-chart stack">
      {data.map((item) => {
        const value = item.value ?? 0;
        const width = `${(value / maxValue) * 100}%`;
        return (
          <div key={item.label} className="metric-bar-row">
            <div className="metric-bar-head">
              <span>{item.label}</span>
              <strong>{formatMetric(item.value)}</strong>
            </div>
            <div className="metric-bar-track">
              <div className="metric-bar-fill" style={{ width, backgroundColor: item.color }} />
            </div>
          </div>
        );
      })}
    </div>
  );
}

function DeliveryTrendChart({ data }: { data: DeliveryTrendDatum[] }) {
  const width = 520;
  const height = 220;
  const padding = 24;
  const maxCount = Math.max(...data.map((point) => point.count), 1);

  const points = data.map((point, index) => {
    const x = padding + (index * (width - padding * 2)) / Math.max(data.length - 1, 1);
    const y = height - padding - (point.count / maxCount) * (height - padding * 2);
    return { ...point, x, y };
  });

  const polylinePoints = points.map((point) => `${point.x},${point.y}`).join(" ");

  return (
    <div className="simple-chart stack">
      <svg viewBox={`0 0 ${width} ${height}`} className="line-chart" aria-label="Deliveries over time">
        <line x1={padding} y1={height - padding} x2={width - padding} y2={height - padding} className="chart-axis" />
        <line x1={padding} y1={padding} x2={padding} y2={height - padding} className="chart-axis" />
        <polyline fill="none" stroke={successColor} strokeWidth="4" points={polylinePoints} />
        {points.map((point) => (
          <circle key={point.minute} cx={point.x} cy={point.y} r="4" fill={successColor} />
        ))}
      </svg>
      <div className="chart-label-row">
        {data.map((point) => (
          <span key={point.minute}>{point.minute}</span>
        ))}
      </div>
    </div>
  );
}

function ReliabilityBars({ data }: { data: ReliabilityDatum[] }) {
  return (
    <div className="simple-chart stack">
      {data.map((item) => (
        <div key={item.name} className="metric-bar-row">
          <div className="metric-bar-head">
            <span>{item.name}</span>
            <strong>{item.success_rate}%</strong>
          </div>
          <div className="metric-bar-track">
            <div
              className="metric-bar-fill"
              style={{ width: `${item.success_rate}%`, backgroundColor: successColor }}
            />
          </div>
        </div>
      ))}
    </div>
  );
}

export default function DashboardCharts({
  endpointStats,
  statusCounts,
  systemStats,
  deliveriesOverTime,
}: DashboardChartsProps) {
  const statusData: DonutSegment[] = [
    { label: "Succeeded", value: statusCounts.succeeded, color: successColor },
    { label: "Failed", value: statusCounts.failed, color: failureColor },
    { label: "Retrying", value: statusCounts.retrying, color: retryingColor },
  ];

  const endpointReliabilityData: ReliabilityDatum[] = endpointStats
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
        <SimpleDonutChart segments={statusData} />
      </div>

      <div className="card">
        <div className="page-header chart-header">
          <h2 className="section-title">Latency</h2>
          <p>Overall system latency from recorded delivery attempts.</p>
        </div>
        <MetricBarChart
          data={[
            { label: "Average latency", value: systemStats?.avg_latency_ms ?? null, color: successColor },
            { label: "P95 latency", value: systemStats?.p95_latency_ms ?? null, color: retryingColor },
          ]}
        />
      </div>

      <div className="card">
        <div className="page-header chart-header">
          <h2 className="section-title">Deliveries over time</h2>
          <p>Delivery volume per minute for the most recent activity window.</p>
        </div>
        <DeliveryTrendChart data={deliveriesOverTime} />
      </div>

      <div className="card">
        <div className="page-header chart-header">
          <h2 className="section-title">Endpoint reliability</h2>
          <p>Success rate highlights reliability differences between active targets.</p>
        </div>
        {endpointReliabilityData.length > 0 ? (
          <ReliabilityBars data={endpointReliabilityData} />
        ) : (
          <p className="muted">Endpoint reliability charts will appear after deliveries have been recorded.</p>
        )}
      </div>
    </div>
  );
}
