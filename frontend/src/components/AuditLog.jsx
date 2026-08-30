export default function AuditLog({ entries }) {
  return (
    <div className="audit-panel">
      <h3 className="display">Audit trail</h3>
      <p className="hint">Every automatic score, override, and escalation — who did it, when, and why. Assumed jurisdiction: HIPAA (US).</p>
      <table className="audit-table">
        <thead>
          <tr><th>Time</th><th>Patient</th><th>Action</th><th>Level change</th><th>Reason</th><th>Actor</th></tr>
        </thead>
        <tbody>
          {entries.map(e => (
            <tr key={e.id}>
              <td className="mono">{new Date(e.timestamp).toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit' })}</td>
              <td>{e.patient_name}</td>
              <td><span className={`action-tag action-${e.action}`}>{e.action.replace('_', ' ')}</span></td>
              <td className="mono">{e.previous_level ?? '—'} → {e.new_level ?? '—'}</td>
              <td className="reason-cell">{e.reason}</td>
              <td>{e.actor}</td>
            </tr>
          ))}
          {entries.length === 0 && <tr><td colSpan={6} className="empty-row">No entries yet.</td></tr>}
        </tbody>
      </table>
    </div>
  );
}
