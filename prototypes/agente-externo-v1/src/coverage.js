export const OPERATIONS = ['Criar Junction', 'Criar Symlink', 'Criar Hardlink', 'Desfazer', 'Remover link', 'Mover arquivos', 'Copiar arquivos'];
export function operationName(row) {
 if (row.operation) return row.operation;
 if (row.action === 'Reversão' || row.action.includes('Desfazer')) return 'Desfazer';
 if (row.action.startsWith('Criação') || row.action === 'Tentativa de Criação') return row.type === 'Junction' ? 'Criar Junction' : row.type === 'Hardlink' ? 'Criar Hardlink' : 'Criar Symlink';
 return row.action;
}
export function formatSize(size) {
 if (size === null || size === undefined) return 'Indisponível';
 return size >= 1048576 ? `${(size / 1048576).toFixed(1)} MiB` : `${(size / 1024).toFixed(1)} KiB`;
}
export function sortedLinks(links, sort, direction) {
 return [...links].sort((a,b) => {
  const cmp = sort === 'size' ? (a.size ?? -1) - (b.size ?? -1) : String(a[sort] || '').localeCompare(String(b[sort] || ''), 'pt-BR', { numeric:true });
  return direction === 'desc' ? -cmp : cmp;
 });
}
export function dateRange(period, now = new Date()) {
 if (period === 'custom') return {};
 const end = new Date(now), start = new Date(now);
 if (period === 'week') start.setDate(start.getDate()-7);
 if (period === 'month') start.setDate(start.getDate()-30);
 const local = d => `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`;
 return period === 'all' ? { from:'',to:'' } : { from: local(start), to:local(end) };
}
