import { LevelBadge, ConfidenceMeter, TrendIcon, StatusPill } from './Badges';

function ageBandLabel(age) {
  if (age < 12) return 'Pediatric';
  if (age > 65) return 'Geriatric';
  return 'Adult';
}

export default function QueueTable({ patients, onSelect }) {
  return (
    <table className="queue-table">
      <thead>
        <tr>
          <th>Priority</th>
          <th>Patient</th>
          <th>Chief complaint</th>
          <th>Confidence</th>
          <th>Wait</th>
          <th>Trend</th>
          <th>Status</th>
        </tr>
      </thead>
      <tbody>
        {patients.map(p => (
          <tr
            key={p.id}
            className={`queue-row ${p.score.fallback_mode ? 'row-fallback' : ''} ${p.status === 'in_review' ? 'row-review' : ''}`}
            onClick={() => onSelect(p)}
            tabIndex={0}
            onKeyDown={(e) => { if (e.key === 'Enter') onSelect(p); }}
          >
            <td><LevelBadge level={p.score.esi_level} /></td>
            <td>
              <div className="patient-name">{p.name}</div>
              <div className="patient-meta mono">{p.age}y · {ageBandLabel(p.age)}</div>
            </td>
            <td className="complaint-cell">{p.chief_complaint}</td>
            <td><ConfidenceMeter confidence={p.score.confidence} band={p.score.confidence_band} /></td>
            <td className="mono">{p.wait_minutes}m</td>
            <td><TrendIcon trend={p.trend} /></td>
            <td><StatusPill status={p.status} /></td>
          </tr>
        ))}
        {patients.length === 0 && (
          <tr><td colSpan={7} className="empty-row">No patients in queue.</td></tr>
        )}
      </tbody>
    </table>
  );
}
