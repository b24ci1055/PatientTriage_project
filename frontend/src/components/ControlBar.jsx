export default function ControlBar({ virtualTime, loadRatio, onAdvance, onSurge, onAddWalkIn, onToggleAudit, auditOpen, busy }) {
  const fallbackMode = loadRatio >= 3.0;
  const timeLabel = virtualTime
    ? new Date(virtualTime).toLocaleString(undefined, { hour: '2-digit', minute: '2-digit', month: 'short', day: 'numeric' })
    : '—';

  return (
    <div className="control-bar">
      <div className="control-bar-left">
        <div className="clock">
          <span className="clock-label">Simulated clock</span>
          <span className="clock-value mono">{timeLabel}</span>
        </div>
        <div className={`mode-indicator ${fallbackMode ? 'mode-fallback' : 'mode-normal'}`}>
          <span className="mode-dot" />
          {fallbackMode ? `Fallback mode — load ${loadRatio.toFixed(1)}×` : `Normal — load ${loadRatio.toFixed(1)}×`}
        </div>
      </div>
      <div className="control-bar-right">
        <button className="btn btn-ghost" disabled={busy} onClick={() => onAddWalkIn()}>+ Add walk-in</button>
        <button className="btn btn-ghost" disabled={busy} onClick={() => onAdvance(15)}>Advance +15 min</button>
        <button className="btn btn-ghost" disabled={busy} onClick={() => onAdvance(60)}>Advance +60 min</button>
        <button className="btn btn-warn" disabled={busy} onClick={() => onSurge(16)}>Simulate surge (3×)</button>
        <button className={`btn ${auditOpen ? 'btn-accent' : 'btn-ghost'}`} onClick={onToggleAudit}>Audit log</button>
      </div>
    </div>
  );
}
