import axios from 'axios';

const BASE = 'http://localhost:8000/api';

export const api = {
  getQueue: () => axios.get(`${BASE}/queue`).then(r => r.data),
  getAuditLog: () => axios.get(`${BASE}/audit-log`).then(r => r.data),
  addPatient: (payload) => axios.post(`${BASE}/patients`, payload).then(r => r.data),
  overridePatient: (id, payload) => axios.post(`${BASE}/patients/${id}/override`, payload).then(r => r.data),
  updateVitals: (id, payload) => axios.post(`${BASE}/patients/${id}/vitals`, payload).then(r => r.data),
  advanceTime: (minutes) => axios.post(`${BASE}/advance-time`, { minutes }).then(r => r.data),
  simulateSurge: (count) => axios.post(`${BASE}/simulate-surge`, { count }).then(r => r.data),
};
