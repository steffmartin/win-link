// Atomic state transitions for fictitious links/history. No filesystem access.
import { isFileLink, normalizePath, undoSummary } from './model.js';

export function historyRecord({ id = crypto.randomUUID(), action, link = null, path = link?.dest || '', type = link?.type || '', status = 'sucesso', outcome = null, metadata = null, date = new Date().toISOString() }) {
  return { id, action, details: type, type, path, source: link?.source || '', linkId: link?.id ?? null, link: link ? { ...link } : null, date, status, outcome, metadata, reverted: false };
}

export function undoError(links, expected, strategy) {
  const link = links.find(item => item.id === expected?.id);
  if (!link || !expected?.source || !expected?.dest || !expected?.type) return 'O link selecionado não está mais disponível. Atualize a lista antes de desfazer.';
  if (normalizePath(link.source) !== normalizePath(expected.source) || normalizePath(link.dest) !== normalizePath(expected.dest) || link.type !== expected.type) return 'O link foi alterado desde a seleção. Revise os caminhos antes de desfazer.';
  if (isFileLink(link.type) && link.status !== 'Ativo') return 'A identidade do arquivo não pôde ser verificada; recupere o acesso e atualize a lista antes de remover o nome.';
  if (isFileLink(link.type) && strategy !== 'remover') return 'Links de arquivo permitem remover apenas o nome selecionado; não use estratégias de diretório.';
  if (!isFileLink(link.type) && !['remover', 'mover', 'duplicar'].includes(strategy)) return 'Selecione uma estratégia válida de restauração.';
  if (strategy !== 'remover' && link.status !== 'Ativo') return 'A origem não está disponível para restaurar arquivos. Verifique o acesso ou remova somente o link.';
  return null;
}

export function canUndoRecord(record, links) {
  return record.action === 'Criação' && record.status === 'sucesso' && !record.reverted && record.linkId !== null && record.linkId !== undefined && record.linkId === record.link?.id && !undoError(links, record.link, 'remover');
}

export function undoOutcome(link, strategy, keepBackup) {
  const file = isFileLink(link.type);
  const effectiveBackup = !file && strategy === 'mover' && Boolean(keepBackup);
  const sourceState = !file && strategy === 'mover' && !effectiveBackup ? 'removed-after-restore' : file ? 'unchanged-file' : 'preserved-directory';
  const targetState = file ? 'removed-name' : strategy === 'remover' ? 'empty-directory' : 'restored-directory';
  return { strategy, keepBackup: effectiveBackup, source: link.source, dest: link.dest, sourceState, targetState, independentCopies: !file && (strategy === 'duplicar' || effectiveBackup), summary: file && link.status !== 'Ativo' ? [`Remover somente o nome ${link.dest}.`, `Os outros nomes e os dados não serão alterados. Confira o acesso a ${link.source}, que está indisponível nesta simulação.`] : undoSummary(link, strategy, effectiveBackup) };
}

export function applyUndo(state, { expected, strategy, keepBackup = false, recordId, date }) {
  const error = undoError(state.links, expected, strategy);
  if (error) throw new Error(error);
  const link = state.links.find(item => item.id === expected.id);
  const outcome = undoOutcome(link, strategy, keepBackup);
  const record = historyRecord({ id: recordId, date, action: 'Reversão', link, outcome, metadata: { strategy, keepBackup: outcome.keepBackup } });
  const originalRecords = state.history.map(row => row.action === 'Criação' && row.status === 'sucesso' && row.linkId === link.id ? { ...row, reverted: true, reversedBy: record.id } : row);
  const paths = { ...(state.paths || {}) };
  paths[normalizePath(link.dest)] = { path: link.dest, kind: outcome.targetState === 'removed-name' ? 'missing' : 'directory', content: outcome.targetState === 'restored-directory' ? 'restored-data' : 'empty' };
  if (outcome.sourceState === 'removed-after-restore') paths[normalizePath(link.source)] = { path: link.source, kind: 'missing' };
  else if (!fileSourceUnavailable(link)) paths[normalizePath(link.source)] = { path: link.source, kind: isFileLink(link.type) ? 'file' : 'directory', content: 'original-data', backup: outcome.keepBackup };
  return { state: { ...state, links: state.links.filter(item => item.id !== link.id), history: [record, ...originalRecords], paths }, record, outcome };
}
function fileSourceUnavailable(link) { return isFileLink(link.type) && link.status !== 'Ativo'; }
