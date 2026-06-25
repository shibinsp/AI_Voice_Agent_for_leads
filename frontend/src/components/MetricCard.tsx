interface MetricCardProps {
  label: string;
  value: string;
  helper: string;
  tone: "lime" | "coral" | "teal" | "ink";
}

export function MetricCard({ label, value, helper, tone }: MetricCardProps) {
  return (
    <article className={`metric-card metric-card--${tone}`}>
      <span className="metric-label">{label}</span>
      <strong className="metric-value">{value}</strong>
      <p className="metric-helper">{helper}</p>
    </article>
  );
}

