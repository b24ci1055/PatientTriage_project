export function LevelBadge({ level, size = 'md' }) {
  return (
    <span className={`level-badge level-${level} size-${size}`} title={`ESI level ${level}`}>
      {level}
    </span>
  );
}

export function ConfidenceMeter({ confidence, band }) {
  const pct = Math.round(confidence * 100);
  return (
    <div className="conf-meter" title={`${pct}% confidence`}>
      <div className="conf-meter-track">
        <div className={`conf-meter-fill conf-${band}`} style={{ width: `${pct}%` }} />
      </div>
      <span className={`conf-label conf-${band}`}>{band} · {pct}%</span>
    </div>
  );
}

export function TrendIcon({ trend }) {
  if (trend === 'worsening') return <span className="trend trend-worsening" title="Worsening trend">&#8593;</span>;
  if (trend === 'improving') return <span className="trend trend-improving" title="Improving trend">&#8595;</span>;
  return <span className="trend trend-stable" title="Stable">&#8212;</span>;
}

export function StatusPill({ status }) {
  const label = { waiting: 'Waiting', in_review: 'Nurse review', seen: 'Seen' }[status] || status;
  return <span className={`status-pill status-${status}`}>{label}</span>;
}
