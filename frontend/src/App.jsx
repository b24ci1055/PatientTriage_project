import { useEffect, useState, useCallback } from 'react';
import { api } from './api';
import ControlBar from './components/ControlBar';
import QueueTable from './components/QueueTable';
import PatientDrawer from './components/PatientDrawer';
import AuditLog from './components/AuditLog';
import WalkInForm from './components/WalkInForm';
import './app.css';

export default function App() {
  const [queue, setQueue] = useState([]);
  const [virtualTime, setVirtualTime] = useState(null);
  const [loadRatio, setLoadRatio] = useState(0);
  const [selected, setSelected] = useState(null);
  const [auditOpen, setAuditOpen] = useState(false);
  const [auditEntries, setAuditEntries] = useState([]);
  const [showWalkIn, setShowWalkIn] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);

  const refresh = useCallback(async () => {
    try {
      const data = await api.getQueue();
      setQueue(data.queue);
      setVirtualTime(data.virtual_time);
      setLoadRatio(data.load_ratio);
      setError(null);
      if (selected) {
        const updated = data.queue.find(p => p.id === selected.id);
        if (updated) setSelected(updated);
      }
    } catch (e) {
      setError('Cannot reach the backend at localhost:8000 — is it running?');
    }
  }, [selected]);

  const refreshAudit = useCallback(async () => {
    const data = await api.getAuditLog();
    setAuditEntries(data.entries);
  }, []);

  useEffect(() => { refresh(); }, []);
  useEffect(() => { if (auditOpen) refreshAudit(); }, [auditOpen, refreshAudit]);

  const withBusy = async (fn) => {
    setBusy(true);
    try { await fn(); await refresh(); if (auditOpen) await refreshAudit(); }
    finally { setBusy(false); }
  };

  const handleAdvance = (minutes) => withBusy(() => api.advanceTime(minutes));
  const handleSurge = (count) => withBusy(() => api.simulateSurge(count));
  const handleOverride = (id, payload) => withBusy(async () => { await api.overridePatient(id, payload); });
  const handleRecheck = (id, vitals) => withBusy(async () => { await api.updateVitals(id, vitals); });
  const handleAddWalkIn = (payload) => withBusy(async () => { await api.addPatient(payload); setShowWalkIn(false); });

  return (
    <div className="app-shell">
      <header className="app-header">
        <div>
          <div className="app-title display">PatientTriage<span className="accent-dot">.ai</span></div>
          <div className="app-subtitle">Continuous, uncertainty-aware triage — Round 2 prototype</div>
        </div>
      </header>

      {error && <div className="callout callout-error">{error}</div>}

      <ControlBar
        virtualTime={virtualTime}
        loadRatio={loadRatio}
        onAdvance={handleAdvance}
        onSurge={handleSurge}
        onAddWalkIn={() => setShowWalkIn(true)}
        onToggleAudit={() => setAuditOpen(o => !o)}
        auditOpen={auditOpen}
        busy={busy}
      />

      <main className="app-main">
        <QueueTable patients={queue} onSelect={setSelected} />
      </main>

      {auditOpen && <AuditLog entries={auditEntries} />}

      {selected && (
        <PatientDrawer
          patient={selected}
          onClose={() => setSelected(null)}
          onOverride={handleOverride}
          onRecheck={handleRecheck}
        />
      )}

      {showWalkIn && (
        <WalkInForm onSubmit={handleAddWalkIn} onClose={() => setShowWalkIn(false)} />
      )}
    </div>
  );
}
