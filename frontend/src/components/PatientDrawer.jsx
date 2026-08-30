import { useState } from 'react';
import { LevelBadge, ConfidenceMeter, StatusPill } from './Badges';

const VITAL_LABELS = {
  heart_rate: 'Heart rate (bpm)',
  resp_rate: 'Resp. rate (/min)',
  spo2: 'SpO2 (%)',
  temp_c: 'Temp (°C)',
  systolic_bp: 'Systolic BP (mmHg)',
};

export default function PatientDrawer({ patient, onClose, onOverride, onRecheck }) {
  const [newLevel, setNewLevel] = useState(patient.score.esi_level);
  const [nurseName, setNurseName] = useState('');
  const [reason, setReason] = useState('');
  const [recheckVitals, setRecheckVitals] = useState({});
  const [tab, setTab] = useState('overview');

  const submitOverride = (e) => {
    e.preventDefault();
    if (!nurseName || !reason) return;
    onOverride(patient.id, { new_level: Number(newLevel), nurse_name: nurseName, reason });
  };

  const submitRecheck = (e) => {
    e.preventDefault();
    onRecheck(patient.id, recheckVitals);
    setRecheckVitals({});
  };

  return (
    <div className="drawer-backdrop" onClick={onClose}>
      <aside className="drawer" onClick={(e) => e.stopPropagation()}>
        <div className="drawer-header">
          <div>
            <h2 className="display">{patient.name}</h2>
            <div className="drawer-subline mono">{patient.age}y · {patient.chief_complaint}</div>
          </div>
          <button className="btn btn-ghost" onClick={onClose}>Close</button>
        </div>

        <div className="drawer-score-row">
          <LevelBadge level={patient.score.esi_level} size="lg" />
          <div>
            <ConfidenceMeter confidence={patient.score.confidence} band={patient.score.confidence_band} />
            <StatusPill status={patient.status} />
          </div>
        </div>

        {patient.score.fallback_mode && (
          <div className="callout callout-warn">
            Scored in fallback mode — system was under surge load, so this used the standard ESI rule table instead of the confidence-weighted model.
          </div>
        )}

        <div className="drawer-tabs">
          <button className={tab === 'overview' ? 'tab-active' : ''} onClick={() => setTab('overview')}>Overview</button>
          <button className={tab === 'override' ? 'tab-active' : ''} onClick={() => setTab('override')}>Override</button>
          <button className={tab === 'recheck' ? 'tab-active' : ''} onClick={() => setTab('recheck')}>Record recheck</button>
        </div>

        {tab === 'overview' && (
          <div className="drawer-section">
            <h3>Why this score</h3>
            <ul className="factor-list">
              {patient.score.contributing_factors.map((f, i) => <li key={i}>{f}</li>)}
            </ul>
            <h3>Vitals on file</h3>
            <table className="vitals-table">
              <tbody>
                {Object.entries(patient.vitals).map(([k, v]) => (
                  <tr key={k}>
                    <td>{VITAL_LABELS[k] || k}</td>
                    <td className="mono">{v === null || v === undefined ? '— not captured —' : v}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            <div className="recheck-note">Recommended recheck interval: <strong>{patient.score.recommended_recheck_minutes} min</strong></div>
          </div>
        )}

        {tab === 'override' && (
          <form className="drawer-section" onSubmit={submitOverride}>
            <p className="hint">The assistant only recommends — a nurse makes the final call. Every override is logged with a reason.</p>
            <label>New ESI level
              <select value={newLevel} onChange={(e) => setNewLevel(e.target.value)}>
                {[1, 2, 3, 4, 5].map(l => <option key={l} value={l}>{l}</option>)}
              </select>
            </label>
            <label>Nurse name
              <input value={nurseName} onChange={(e) => setNurseName(e.target.value)} placeholder="e.g. Nurse Kapoor" />
            </label>
            <label>Reason (required — becomes part of the audit trail)
              <textarea value={reason} onChange={(e) => setReason(e.target.value)} rows={3} />
            </label>
            <button className="btn btn-accent" type="submit">Save override</button>
          </form>
        )}

        {tab === 'recheck' && (
          <form className="drawer-section" onSubmit={submitRecheck}>
            <p className="hint">Simulate a vitals recheck while waiting. The system re-scores and flags any worsening trend.</p>
            {Object.entries(VITAL_LABELS).map(([key, label]) => (
              <label key={key}>{label}
                <input
                  type="number"
                  step="0.1"
                  placeholder={patient.vitals[key] ?? ''}
                  value={recheckVitals[key] ?? ''}
                  onChange={(e) => setRecheckVitals({ ...recheckVitals, [key]: e.target.value === '' ? null : Number(e.target.value) })}
                />
              </label>
            ))}
            <button className="btn btn-accent" type="submit">Submit recheck</button>
          </form>
        )}
      </aside>
    </div>
  );
}
