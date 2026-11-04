import { operationName } from './coverage.js';
export const DEFAULTS = { theme: 'dark', type: 'Junction', directories: 'C:\\Links', backup: true, notifications: true, nested: true, logs: 'INFO' };
export function validatePreferences(p) {
  const paths = p.directories.split(/\r?\n/).map(s => s.trim().replaceAll('/', String.fromCharCode(92))).filter(Boolean);
  if (!paths.length) return ['Configure pelo menos um diretório de descoberta.'];
  return paths.every(s => /^(?:[a-z]:\\|\\\\[^\\]+\\[^\\]+)/i.test(s)) ? [] : ['Use diretórios absolutos, um por linha.'];
}
export function loadPreferences() {
  try {
    const p = JSON.parse(localStorage.getItem('winlink-demo-preferences'));
    if (!p || typeof p.directories !== 'string' || validatePreferences(p).length || !['auto', 'dark', 'light'].includes(p.theme) || !['Junction', 'Symlink (Dir)', 'Symlink (File)', 'Hardlink'].includes(p.type) || !['DEBUG','INFO','WARNING','ERROR','CRITICAL'].includes(p.logs) || ['backup','notifications','nested'].some(k => typeof p[k] !== 'boolean')) return { ...DEFAULTS };
    return { ...DEFAULTS, ...p };
  } catch { return { ...DEFAULTS }; }
}
export function filterHistory(rows, f) {
  return rows.filter(r => {
    const d = new Date(r.date), date = `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`;
    return (!f.operation || operationName(r) === f.operation) && (!f.type || r.type === f.type) && (!f.result || r.status.startsWith(f.result)) && (!f.from || date >= f.from) && (!f.to || date <= f.to);
  });
}
