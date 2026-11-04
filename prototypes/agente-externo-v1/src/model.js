// Regras da demonstração: não lê arquivos nem consulta a API do Windows.
export const TYPES = ['Junction', 'Symlink (Dir)', 'Symlink (File)', 'Hardlink'];
export const isFileLink = type => type === 'Hardlink' || type === 'Symlink (File)';

export function normalizePath(value = '') {
  const raw = value.trim().replaceAll('/', '\\');
  const unc = raw.startsWith('\\\\');
  const parts = raw.slice(unc ? 2 : 0).split('\\');
  const clean = [];
  const rootLength = unc ? 2 : 1;
  for (const part of parts) {
    if (!part || part === '.') continue;
    if (part === '..') { if (clean.length > rootLength) clean.pop(); }
    else clean.push(part);
  }
  return ((unc ? '\\\\' : '') + clean.join('\\')).toLowerCase();
}
export function volume(path) {
  const value = normalizePath(path);
  return value.startsWith('\\\\') ? value.split('\\').slice(0, 4).join('\\') : value.slice(0, 2);
}
const overlaps = (a, b) => a === b || a.startsWith(b + '\\') || b.startsWith(a + '\\');

function pathErrors(value, label) {
  if (!value.trim()) return [`${label}: preencha o caminho.`];
  const path = value.trim().replaceAll('/', '\\');
  if (path.startsWith('\\\\?\\') || path.startsWith('\\\\.\\')) return [`${label}: caminhos de dispositivo ou com prefixo estendido não fazem parte desta demonstração.`];
  const local = /^[a-z]:\\/i.test(path);
  const unc = /^\\\\[^\\]+\\[^\\]+(?:\\|$)/.test(path);
  if (!local && !unc) return [`${label}: use um caminho absoluto, como D:\\Dados\\Projetos.`];
  const segments = path.slice(local ? 3 : 2).split('\\').filter(Boolean);
  const errors = [];
  if (/[<>"|?*\x00-\x1f]/.test(path) || path.slice(local ? 2 : 0).includes(':')) errors.push(`${label}: há caracteres inválidos no caminho.`);
  const reserved = /^(con|prn|aux|nul|com[1-9¹²³]|lpt[1-9¹²³])(?:\.|$)/i;
  if (segments.some(segment => segment !== '.' && segment !== '..' && (/[. ]$/.test(segment) || reserved.test(segment)))) errors.push(`${label}: evite nomes reservados e nomes terminados em ponto ou espaço.`);
  const normalized = normalizePath(path);
  if (normalized === volume(normalized)) errors.push(`${label}: não use a raiz de um disco ou compartilhamento.`);
  return errors;
}

// Resolve somente os links fictícios conhecidos para identificar aliases/ciclos.
function resolveDemoPath(value, links) {
  let current = normalizePath(value);
  const seen = new Set();
  for (let step = 0; step <= links.length; step++) {
    if (seen.has(current)) return null;
    seen.add(current);
    const match = [...links].sort((a, b) => b.dest.length - a.dest.length).find(link => {
      const dest = normalizePath(link.dest);
      return current === dest || (!isFileLink(link.type) && current.startsWith(dest + '\\'));
    });
    if (!match) return current;
    const dest = normalizePath(match.dest);
    current = normalizePath(match.source) + current.slice(dest.length);
  }
  return null;
}

export function validateCreation({ source = '', dest = '', type, sourceExists = true, targetExists = false, sourceKind = isFileLink(type) ? 'file' : 'directory', targetKind = targetExists ? (isFileLink(type) ? 'file' : 'directory') : 'missing', copyConflicts = false, existingLinks = [] }) {
  const errors = [...pathErrors(source, 'Local dos dados'), ...pathErrors(dest, 'Caminho do link')];
  if (!TYPES.includes(type)) errors.push('Selecione um dos quatro tipos de link disponíveis.');
  if (errors.length) return [...new Set(errors)];
  const a = normalizePath(source), b = normalizePath(dest);
  if (overlaps(a, b)) errors.push('Escolha caminhos diferentes, sem colocar um dentro do outro.');
  const existingTarget = existingLinks.find(link => normalizePath(link.dest) === b);
  if (existingTarget || targetKind === 'link') errors.push('O caminho do link já é um link. Ele será preservado; escolha outro nome.');
  if (isFileLink(type)) {
    if (!sourceExists || sourceKind !== 'file') errors.push('Links de arquivo exigem um arquivo existente no local dos dados.');
    if (targetExists || targetKind !== 'missing') errors.push('O caminho do novo link de arquivo já existe. Escolha outro nome.');
  } else {
    if (sourceExists && sourceKind !== 'directory') errors.push('O local dos dados deve ser uma pasta para este tipo de link.');
    if (targetKind !== 'missing' && targetKind !== 'directory' && targetKind !== 'link') errors.push('O caminho do link contém um arquivo. A migração de diretórios exige uma pasta ou um novo caminho.');
    if (targetKind === 'directory' && sourceExists && copyConflicts) errors.push('Há arquivos com o mesmo nome nas duas pastas. Resolva os conflitos antes de migrar; nada será sobrescrito automaticamente.');
  }
  if (type === 'Hardlink' && volume(a) !== volume(b)) errors.push('Hard links precisam estar no mesmo volume.');
  if (type === 'Junction' && (a.startsWith('\\\\') || b.startsWith('\\\\'))) errors.push('Para junctions, use caminhos de discos locais. Para uma pasta de rede, avalie um link simbólico.');
  if (existingLinks.length && !existingTarget) {
    const resolvedSource = resolveDemoPath(a, existingLinks), resolvedTarget = resolveDemoPath(b, existingLinks);
    if (!resolvedSource || !resolvedTarget || overlaps(resolvedSource, resolvedTarget)) errors.push('Os caminhos resolvem para locais iguais, sobrepostos ou cíclicos por meio de um link já existente.');
    if (existingLinks.some(link => b.startsWith(normalizePath(link.dest) + '\\'))) errors.push('O novo caminho passa por um link existente. Escolha um local direto para evitar alterar outra árvore de dados.');
  }
  return [...new Set(errors)];
}

export function undoSummary(link, strategy, keepBackup) {
  if (isFileLink(link.type)) return [`Remover somente o nome ${link.dest}.`, `Preservar o arquivo acessível por ${link.source}; os dados não serão apagados.`];
  if (strategy === 'remover') return [`Remover o link e deixar uma pasta normal vazia em ${link.dest}.`, `Preservar todos os dados em ${link.source}.`];
  if (strategy === 'duplicar') return [`Restaurar os arquivos em uma pasta normal em ${link.dest}.`, `Manter os dados em ${link.source}. As duas pastas serão cópias independentes.`];
  return [`Restaurar os arquivos em uma pasta normal em ${link.dest}.`, keepBackup ? `Manter ${link.source} como backup dos dados.` : `Remover ${link.source} somente depois de concluir a restauração.`];
}
export const defaults = { theme: 'dark', directories: ['C:\\Dados', 'D:\\Arquivo'], notifications: true, keepBackup: true, warnNested: true, logLevel: 'INFO' };
export const initialLinks = [
  { id: 'link-1', name: 'Projetos', source: 'D:\\Arquivo\\Projetos', dest: 'C:\\Dados\\Projetos', type: 'Junction', status: 'Ativo', creator: 'App', size: '124 MB', files: 82, folders: 9, date: '2026-11-03T10:20:00' },
  { id: 'link-2', name: 'Configuração', source: 'D:\\Arquivo\\Configuracao', dest: 'C:\\Dados\\Configuracao', type: 'Symlink (Dir)', status: 'Ativo', creator: 'Existente', size: '12 MB', files: 14, folders: 2, date: '2026-11-02T09:10:00' },
  { id: 'link-3', name: 'Relatório — outro nome', source: 'C:\\Dados\\relatorio.txt', dest: 'C:\\Dados\\Referencias\\relatorio.txt', type: 'Hardlink', status: 'Ativo', creator: 'App', size: '8 KB', files: 1, folders: 0, date: '2026-11-03T10:25:00' },
  { id: 'link-4', name: 'Pasta indisponível', source: 'E:\\Dados\\Projetos', dest: 'C:\\Dados\\ProjetosExternos', type: 'Symlink (Dir)', status: 'Quebrado', creator: 'Existente', size: 'Indisponível', date: '2026-10-30T11:30:00' },
  { id: 'link-5', name: 'Acesso restrito', source: 'D:\\Restrito', dest: 'C:\\Dados\\Restrito', type: 'Junction', status: 'Inacessível', creator: 'Existente', size: 'Indisponível', date: '2026-10-29T15:00:00' },
];
