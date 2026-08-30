import { useState } from 'react';

export default function WalkInForm({ onSubmit, onClose }) {
  const [form, setForm] = useState({
    name: '', age: '', chief_complaint: '', has_history: false,
    heart_rate: '', resp_rate: '', spo2: '', temp_c: '', systolic_bp: '',
  });

  const set = (key) => (e) => {
    const val = e.target.type === 'checkbox' ? e.target.checked : e.target.value;
    setForm({ ...form, [key]: val });
  };

  const submit = (e) => {
    e.preventDefault();
    const numOrNull = (v) => (v === '' ? null : Number(v));
    onSubmit({
      name: form.name, age: Number(form.age), chief_complaint: form.chief_complaint,
      has_history: form.has_history,
      heart_rate: numOrNull(form.heart_rate), resp_rate: numOrNull(form.resp_rate),
      spo2: numOrNull(form.spo2), temp_c: numOrNull(form.temp_c), systolic_bp: numOrNull(form.systolic_bp),
    });
  };

  return (
    <div className="drawer-backdrop" onClick={onClose}>
      <aside className="drawer" onClick={(e) => e.stopPropagation()}>
        <div className="drawer-header">
          <h2 className="display">New walk-in intake</h2>
          <button className="btn btn-ghost" onClick={onClose}>Close</button>
        </div>
        <form className="drawer-section" onSubmit={submit}>
          <p className="hint">Vitals left blank simulate realistic first-minute data gaps — the assistant is built to score on what's actually available.</p>
          <label>Name<input required value={form.name} onChange={set('name')} /></label>
          <label>Age<input required type="number" value={form.age} onChange={set('age')} /></label>
          <label>Chief complaint<input required value={form.chief_complaint} onChange={set('chief_complaint')} /></label>
          <label className="checkbox-row"><input type="checkbox" checked={form.has_history} onChange={set('has_history')} /> Prior health record on file</label>
          <label>Heart rate (bpm)<input type="number" value={form.heart_rate} onChange={set('heart_rate')} /></label>
          <label>Resp. rate (/min)<input type="number" value={form.resp_rate} onChange={set('resp_rate')} /></label>
          <label>SpO2 (%)<input type="number" value={form.spo2} onChange={set('spo2')} /></label>
          <label>Temp (°C)<input type="number" step="0.1" value={form.temp_c} onChange={set('temp_c')} /></label>
          <label>Systolic BP (mmHg)<input type="number" value={form.systolic_bp} onChange={set('systolic_bp')} /></label>
          <button className="btn btn-accent" type="submit">Score &amp; add to queue</button>
        </form>
      </aside>
    </div>
  );
}
