import React, { useState, useEffect, useRef } from 'react';
import {
  Folder, File, Link as LinkIcon, Search, Filter,
  Plus, Trash2, Copy, CornerUpLeft, CheckCircle,
  XCircle, AlertTriangle, Moon, Sun, MoreVertical,
  Settings, Clock, Info, ShieldAlert, ArrowRight,
  Save, X, FolderOpen, Download, HardDrive, Keyboard
} from 'lucide-react';
import { isFileLink, normalizePath, undoSummary, validateCreation } from './model.js';
import { OPERATIONS, operationName, formatSize, sortedLinks, dateRange } from './coverage.js';
import { DEFAULTS, loadPreferences, filterHistory, validatePreferences } from './controls.js';
import { historyRecord, canUndoRecord, undoError, applyUndo } from './history.js';

// --- Dados Iniciais ---
const mockInitialLinks = [
  { id: 1, name: 'Projetos_Antigos', source: 'C:\\Projetos\\2022', dest: 'D:\\Archive\\2022', type: 'Junction', status: 'Ativo', creator: 'App', size: 44040192, files: 128, folders: 12, date: '2023-10-01' },
  { id: 2, name: 'Config_Global', source: 'C:\\Users\\Admin\\.config', dest: 'E:\\Sync\\.config', type: 'Symlink (Dir)', status: 'Ativo', creator: 'Existente', size: 2097152, files: 32, folders: 4, date: '2023-10-05' },
  { id: 3, name: 'hosts_backup', source: 'C:\\Windows\\System32\\drivers\\etc\\hosts', dest: 'C:\\Backup\\hosts_win', type: 'Hardlink', status: 'Ativo', creator: 'Manual', size: 24576, files: 1, folders: 0, date: '2023-10-10' },
];

mockInitialLinks.push({ id: 4, name: 'Fotos_Offline', source: 'F:/Fotos', dest: 'C:/Links/Fotos', type: 'Symlink (Dir)', status: 'Inacessível', creator: 'Existente', size: null, date: '2023-10-11' }, { id: 5, name: 'Pasta_Removida', source: 'D:/Ausente', dest: 'C:/Links/Ausente', type: 'Junction', status: 'Quebrado', creator: 'Manual', size: null, date: '2023-10-12' });

mockInitialLinks.push({ id: 6, name: 'Arquivo_Indisponivel', source: 'F:/Dados/arquivo.txt', dest: 'C:/Links/arquivo-offline.txt', type: 'Symlink (File)', status: 'Inacessível', creator: 'Existente', size:null, date:'2023-10-12' });

const initialDemo = () => ({
  links: mockInitialLinks.map(link => ({ ...link })),
  history: [historyRecord({ id: 'initial-creation-1', action: 'Criação', link: mockInitialLinks[0], date: `${mockInitialLinks[0].date}T12:00:00-03:00` })],
  paths: {},
});

export default function WinLinkApp() {
  // --- Estados Globais ---
  const [darkMode, setDarkMode] = useState(() => loadPreferences().theme === 'auto' ? window.matchMedia('(prefers-color-scheme: dark)').matches : loadPreferences().theme !== 'light');
  const [currentScreen, setCurrentScreen] = useState('principal'); // principal, criar, progresso, historico, config, propriedades

  // Dados simulados
  const [demo, setDemo] = useState(initialDemo);
  const demoRef = useRef(demo);
  demoRef.current = demo;
  const { links, history: historyLog } = demo;
  const commitDemo = transform => {
    const next = transform(demoRef.current);
    demoRef.current = next;
    setDemo(next);
    return next;
  };
  const setHistoryLog = value => commitDemo(prev => ({ ...prev, history: typeof value === 'function' ? value(prev.history) : value }));
  const [selectedItem, setSelectedItem] = useState(null); // Usado para propriedades e reversão

  // Modais e Popups
  const [activeDialog, setActiveDialog] = useState(null); // null, 'selector', 'filter', 'confirmUndo', 'message'
  const [dialogConfig, setDialogConfig] = useState({});

  // --- Estados: Principal ---
  const [searchQuery, setSearchQuery] = useState('');
  const [principalViewMode, setPrincipalViewMode] = useState('normal'); // normal, compact, scanning

  // --- Estados: Criar ---
  const [linkType, setLinkType] = useState(() => loadPreferences().type);
  const [sourcePath, setSourcePath] = useState('');
  const [destPath, setDestPath] = useState('');
  const [sourceEntry, setSourceEntry] = useState(() => isFileLink(loadPreferences().type) ? 'file' : 'directory'); // directory, file, missing
  const [targetEntry, setTargetEntry] = useState('missing'); // directory, file, link, missing
  const [copyConflicts, setCopyConflicts] = useState(false);
  const [creationErrors, setCreationErrors] = useState([]);
  const [simulateErrorType, setSimulateErrorType] = useState('none'); // none, occupied, space, permission, unavailable

  // --- Estados: Progresso ---
  const [progressValue, setProgressValue] = useState(0);
  const [progressStatus, setProgressStatus] = useState('idle'); // idle, processing, cancelled, success, error
  const [progressMessage, setProgressMessage] = useState('');
  const timerRef = useRef(null);
  const operationRef = useRef(null);

  // --- Estados: Desfazer ---
  const [undoStrategy, setUndoStrategy] = useState('mover');
  const [keepBackup, setKeepBackup] = useState(false);

  const [preferences, setPreferences] = useState(loadPreferences);
  const [draft, setDraft] = useState(loadPreferences);
  const [linkFilter, setLinkFilter] = useState({ type: '', status: '', creator: '' });
  const [filterDraft, setFilterDraft] = useState({ type: '', status: '', creator: '' });
  const [historyFilter, setHistoryFilter] = useState({ type: '', result: '', from: '', to: '', operation: '', period: 'all' });
  const [sort, setSort] = useState('dest');
  const [sortDirection, setSortDirection] = useState('asc');
  const [previewScenario, setPreviewScenario] = useState('normal');
  const [historyScenario, setHistoryScenario] = useState('normal');
  const [undoScenario, setUndoScenario] = useState('none');
  const [statsMode, setStatsMode] = useState('ready');
  const [folderScenario, setFolderScenario] = useState('available');
  const [initialCache, setInitialCache] = useState('ready');
  const [lastScan, setLastScan] = useState('Exemplos fictícios carregados; nenhum disco consultado.');
  const [progressKind, setProgressKind] = useState('creation');
  const [undoReturn, setUndoReturn] = useState('principal');
  const [cacheError, setCacheError] = useState(false);
  const [cacheScenario, setCacheScenario] = useState('success');
  const modalRef = useRef(null);
  const returnFocus = useRef(null);
  useEffect(() => {
    if (!activeDialog) return;
    const previous = returnFocus.current || document.activeElement;
    const panel = modalRef.current;
    const focusables = () => [...panel.querySelectorAll('button, input, select, textarea, [tabindex="0"]')].filter(el => !el.disabled && el.getClientRects().length);
    (focusables()[0] || panel).focus();
    const key = event => {
      if (event.key === 'Escape') { event.preventDefault(); closeDialog(); }
      if (event.key === 'Tab') {
        const nodes = focusables(), first = nodes[0], last = nodes.at(-1);
        if (!first) { event.preventDefault(); panel.focus(); }
        else if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
        else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
      }
    };
    panel.addEventListener('keydown', key);
    return () => { panel.removeEventListener('keydown', key); if (previous?.isConnected) previous.focus(); };
  }, [activeDialog]);
  useEffect(() => {
    if (principalViewMode !== 'scanning') return;
    const timer = setTimeout(() => { setCacheError(cacheScenario === 'failure'); setInitialCache('ready'); setLastScan(cacheScenario === 'failure' ? 'Atualização falhou; último cache fictício mantido.' : 'Descoberta simulada atualizada agora.'); setPrincipalViewMode('normal'); }, 900);
    return () => clearTimeout(timer);
  }, [principalViewMode, cacheScenario]);
  const exportHistory = () => {
    if (historyScenario === 'export') return showDialog('message', { type: 'error', title: 'Exportação não realizada', message: 'Simulação de falha ao gravar JSON. Os registros foram preservados. Escolha o cenário Normal e tente novamente.' });
    const blob = new Blob([JSON.stringify({ demonstration: true, exportedAt: new Date().toISOString(), records: historyLog }, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob), anchor = document.createElement('a');
    anchor.href = url; anchor.download = 'winlink-historico-demo.json'; anchor.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  };
  const savePreferences = () => {
    const errors = validatePreferences(draft);
    if (errors.length) return showDialog('message', { type: 'error', title: 'Revise as preferências', message: errors.join('\n') });
    try { localStorage.setItem('winlink-demo-preferences', JSON.stringify(draft)); }
    catch { return showDialog('message', { type: 'error', title: 'Preferências não salvas', message: 'O navegador bloqueou o armazenamento local. As preferências anteriores foram mantidas.' }); }
    setPreferences({ ...draft }); setDarkMode(draft.theme === 'auto' ? window.matchMedia('(prefers-color-scheme: dark)').matches : draft.theme === 'dark'); setLinkType(draft.type); setSourceEntry(isFileLink(draft.type) ? 'file' : 'directory');
    showDialog('message', { type: 'success', title: 'Preferências salvas', message: 'Salvas somente neste navegador para a demonstração. Não alteram o Windows. Tema, tipo padrão e backup são aplicados à demo; diretórios, avisos, notificações e logs são especificações para a implementação PyQt6.' });
  };
  // Aplicar tema
  useEffect(() => {
    document.documentElement.classList.toggle('dark', darkMode);
  }, [darkMode]);

  useEffect(() => {
    if (preferences.theme !== 'auto') return;
    const media = window.matchMedia('(prefers-color-scheme: dark)');
    const change = () => setDarkMode(media.matches);
    media.addEventListener('change', change);
    return () => media.removeEventListener('change', change);
  }, [preferences.theme]);
  useEffect(() => {
    if (statsMode !== 'loading') return;
    const timer = setTimeout(() => setStatsMode('ready'), 900);
    return () => clearTimeout(timer);
  }, [statsMode, selectedItem?.id]);
  useEffect(() => {
    const key = event => {
      if (activeDialog || operationRef.current) return;
      const mod = event.ctrlKey || event.metaKey;
      if (event.key === 'F5') { event.preventDefault(); setCurrentScreen('principal'); setPrincipalViewMode('scanning'); }
      if (!mod) return;
      const screen = { n:'criar', ',':'config', h:'historico' }[event.key.toLowerCase()];
      if (screen) { event.preventDefault(); setCurrentScreen(screen); }
      if (event.key.toLowerCase() === 'f') { event.preventDefault(); setCurrentScreen('principal'); requestAnimationFrame(() => document.querySelector('[aria-label="Buscar links"]')?.focus()); }
      if (event.key.toLowerCase() === 'q') { event.preventDefault(); showDialog('message', { type:'warning', title:'Sair do WinLink', message:'Na aplicação Windows, Ctrl+Q fecha a janela. A demo permanece aberta para revisão; use o controle de fechar a aba para sair.' }); }
    };
    window.addEventListener('keydown', key);
    return () => window.removeEventListener('keydown', key);
  }, [activeDialog]);
  const describeOpen = (path, unavailable = false) => showDialog('message', {
    type: unavailable || folderScenario === 'missing' ? 'warning' : 'success',
    title: unavailable || folderScenario === 'missing' ? 'Caminho indisponível' : 'Abrir no Explorador',
    message: unavailable || folderScenario === 'missing' ? `O caminho ${path} está indisponível nesta simulação. Verifique acesso e conexão; nenhum Explorer foi aberto.` : `Na aplicação Windows, abrir ou localizar este caminho no Explorador: ${path}. Esta demo apenas representa a ação; não abre arquivos reais.`,
  });
  const chooseDirectory = value => {
    setDraft(d => ({ ...d, directories: [...new Set([...d.directories.split(/\r?\n/).map(p=>p.trim()).filter(Boolean), value])].join('\n') })); closeDialog();
  };
  const loadHistoryExamples = () => setHistoryLog(prev => [
    ...OPERATIONS.filter(op => !prev.some(row => row.metadata?.exampleOperation === op)).map((op,index) => historyRecord({ action:op, type:op.includes('Hardlink') ? 'Hardlink' : op.includes('Symlink') ? 'Symlink (Dir)' : 'Junction', path:`C:/Exemplos/Operacao-${index+1}`, status:index === 4 ? 'erro: acesso negado (exemplo)' : 'sucesso', metadata:{exampleOperation:op}, date:new Date(Date.now()-index*86400000).toISOString() })), ...prev,
  ]);
  const clearHistory = () => {
    if (historyScenario === 'clear') return showDialog('message', { type:'error', title:'Histórico não foi limpo', message:'Falha simulada na gravação. Todos os registros foram mantidos. Selecione Normal e tente novamente.' });
    setHistoryLog([]); closeDialog();
  };
  // Limpeza de timer no unmount
  useEffect(() => {
    return () => { stopProgressTimer(); operationRef.current = null; };
  }, []);

  // --- Helpers de Progresso ---
  const stopProgressTimer = () => {
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
  };

  const creationSnapshot = () => {
    const source = sourcePath.trim(), dest = destPath.trim();
    const knownSource = demoRef.current.paths[normalizePath(source)];
    const knownTarget = demoRef.current.paths[normalizePath(dest)];
    const sourceKind = knownSource?.kind || sourceEntry;
    const targetKind = knownTarget?.kind || targetEntry;
    return { source, dest, type: linkType, sourceExists: sourceKind !== 'missing', sourceKind,
      targetExists: targetKind !== 'missing', targetKind, copyConflicts, simulateErrorType, previewScenario };
  };

  const showValidation = (errors) => {
    setCreationErrors(errors);
    showDialog('message', { type: 'error', title: 'Revise os caminhos', message: errors.join('\n') });
  };

  const handleCreateConfirm = () => {
    if (operationRef.current) return;
    const snapshot = creationSnapshot();
    if (snapshot.previewScenario === 'space' && snapshot.targetKind !== 'directory') return showValidation(['Para demonstrar espaço insuficiente na prévia, escolha uma pasta com arquivos no caminho do novo link.']);
    if (snapshot.simulateErrorType === 'backup' && (isFileLink(snapshot.type) || snapshot.targetKind !== 'directory')) return showValidation(['O cenário de backup preservado exige migração de uma pasta existente no caminho do link.']);
    const errors = validateCreation({ ...snapshot, existingLinks: links });
    if (errors.length) { showValidation(errors); return; }
    setCreationErrors([]);
    showDialog('confirmCreate', snapshot);
  };

  const executeCreation = () => {
    if (operationRef.current) return;
    // Recheck the exact scenario the user reviewed, against the current demo links.
    const snapshot = { ...dialogConfig };
    if (['space', 'calculating', 'processes'].includes(snapshot.previewScenario)) return showValidation(['A prévia ainda não permite confirmar. Revise o espaço ou aguarde o cálculo.']);
    const errors = validateCreation({ ...snapshot, existingLinks: links });
    if (errors.length) { showValidation(errors); return; }
    operationRef.current = snapshot;
    closeDialog();
    setCurrentScreen('progresso');
    setProgressKind('creation');
    setProgressStatus('processing');
    setProgressValue(0);
    setProgressMessage('Iniciando operação simulada...');
    let value = 0;
    timerRef.current = setInterval(() => {
      if (operationRef.current !== snapshot) return;
      value += 20;
      if (value === 40) setProgressMessage('Verificando permissões e espaço...');
      if (value === 60 && !['none', 'backup', 'history'].includes(snapshot.simulateErrorType)) {
        stopProgressTimer();
        operationRef.current = null;
        setProgressStatus('error');
        handleSimulatedError(snapshot.simulateErrorType, snapshot);
        return;
      }
      if (value === 60) setProgressMessage(snapshot.targetKind === 'directory' ? 'Copiando e preservando os arquivos da pasta anterior...' : 'Preparando o novo caminho...');
      if (value === 80) setProgressMessage('Criando o link de demonstração...');
      setProgressValue(value);
      if (value >= 100) {
        stopProgressTimer();
        operationRef.current = null;
        const novoLink = {
          id: crypto.randomUUID(), name: snapshot.dest.replaceAll('/', '\\').split('\\').filter(Boolean).pop(),
          source: snapshot.source, dest: snapshot.dest, type: snapshot.type,
          status: 'Ativo', creator: 'App', size: isFileLink(snapshot.type) ? 24576 : 44040192, files: isFileLink(snapshot.type) ? 1 : 128, folders: isFileLink(snapshot.type) ? 0 : 12, date: new Date().toISOString(),
        };
        const log = historyRecord({ action: 'Criação', link: novoLink, metadata: { backupPreserved: snapshot.simulateErrorType === 'backup', targetKindBefore: snapshot.targetKind, sourceExistsBefore: snapshot.sourceExists } });
        commitDemo(prev => ({ ...prev, links: [...prev.links, novoLink], history: snapshot.simulateErrorType === 'history' ? prev.history : [log, ...prev.history],
          paths: { ...prev.paths,
            [normalizePath(novoLink.dest)]: { path: novoLink.dest, kind: 'link' },
            [normalizePath(novoLink.source)]: { path: novoLink.source, kind: isFileLink(novoLink.type) ? 'file' : 'directory', content: 'original-data' },
          },
        }));
        setProgressStatus('success');
        setProgressMessage(snapshot.targetKind === 'directory' ? 'Migração simulada concluída: arquivos preservados no local dos dados e pasta anterior substituída pelo link.' : 'Operação simulada concluída. Nenhum arquivo real foi alterado.');
        if (snapshot.simulateErrorType === 'backup') setProgressMessage(`Link criado. Backup fictício preservado em ${snapshot.dest}.winlink-backup. Confira os dados antes de removê-lo; nenhum arquivo real foi alterado.`);
        if (snapshot.simulateErrorType === 'history') setProgressMessage('Link criado e listado, mas o registro do histórico falhou nesta simulação. Não repita a criação. Consulte a lista; a reversão permanece disponível nas propriedades.');
      }
    }, 600);
  };

  const handleSimulatedError = (errType, snapshot) => {
    let msg = '';
    switch(errType) {
      case 'occupied': msg = 'O destino já está ocupado por outro arquivo ou pasta.'; break;
      case 'space': msg = 'Espaço em disco insuficiente no volume de destino.'; break;
      case 'permission': msg = 'Permissão negada. Verifique acesso à pasta e, para symlinks, Modo de Desenvolvedor ou permissões apropriadas.'; break;
      case 'unavailable': msg = 'O caminho de origem está indisponível ou desconectado.'; break;
      default: msg = 'Erro desconhecido.';
    }
    setProgressMessage(msg);
    addHistoryRecord('Tentativa de Criação', snapshot.type, snapshot.dest, 'erro: ' + msg);
  };

  const handleCancelProgress = () => {
    if (!operationRef.current) return;
    const cancelled = operationRef.current;
    operationRef.current = null;
    stopProgressTimer();
    setProgressStatus('cancelling');
    setProgressMessage('Cancelando / preservando dados…');
    operationRef.current = { cancelling: true };
    timerRef.current = setTimeout(() => {
      operationRef.current = null; timerRef.current = null;
      setProgressStatus('cancelled');
      setProgressMessage('Cancelamento concluído. Dados originais preservados; nenhum link adicionado.');
      if (cancelled.kind === 'undo') setHistoryLog(prev => [historyRecord({ action: 'Desfazer (Cancelado)', link: cancelled.expected, status: 'cancelado' }), ...prev]);
      else addHistoryRecord('Criação (Cancelada)', linkType, destPath, 'cancelado');
    }, 700);
  };

  const resetCreation = () => {
    if (operationRef.current) return;
    if (progressKind === 'undo') { setCurrentScreen(undoReturn); return; }
    setCreationErrors([]);
    setProgressStatus('idle');
    setProgressValue(0);
    setCurrentScreen('criar');
  };

  const addHistoryRecord = (action, details, path, status) => {
    const record = historyRecord({ action, path, type: details, status });
    setHistoryLog(prev => [record, ...prev]);
  };

  // --- Helpers de Dialog ---
  const showDialog = (type, config = {}) => {
    if (!activeDialog) returnFocus.current = document.activeElement;
    if (type === 'filter') setFilterDraft({ ...linkFilter });
    setDialogConfig(config);
    setActiveDialog(type);
  };
  const closeDialog = () => {
    setActiveDialog(null);
    setDialogConfig({});
  };

  const openSelector = (setterType) => {
    showDialog('selector', {
      setter: setterType, // 'source' or 'dest'
      isDir: linkType !== 'Symlink (File)' && linkType !== 'Hardlink'
    });
  };

  const handleSelectorPick = (val) => {
    if (dialogConfig.setter === 'source') { setSourcePath(val); setSourceEntry(dialogConfig.isDir ? 'directory' : 'file'); }
    if (dialogConfig.setter === 'dest') { setDestPath(val); setTargetEntry('missing'); }
    closeDialog();
  };

  const openUndo = (link) => {
    if (operationRef.current) return;
    const error = undoError(demoRef.current.links, link, 'remover');
    if (error) { showDialog('message', { type: 'error', title: 'Link indisponível', message: error }); return; }
    const current = demoRef.current.links.find(item => item.id === link.id);
    if (isFileLink(current.type) && current.status !== 'Ativo') return showDialog('message', { type:'error', title:'Identidade não verificada', message:'A origem do arquivo está indisponível. O aplicativo bloqueia a remoção até verificar a identidade do link. Atualize a lista após recuperar o acesso.' });
    setUndoScenario('none');
    setSelectedItem(current);
    setUndoStrategy(isFileLink(current.type) || current.status !== 'Ativo' ? 'remover' : 'mover');
    setKeepBackup(preferences.backup);
    showDialog('confirmUndo', { item: { ...current }, returnTo: currentScreen });
  };

  const executeUndo = () => {
    if (operationRef.current) return;
    const expected = dialogConfig.item, returnTo = dialogConfig.returnTo;
    const strategy = isFileLink(expected?.type) ? 'remover' : undoStrategy;
    const operation = { kind:'undo', expected, strategy, keepBackup, scenario:undoScenario };
    const error = undoError(demoRef.current.links, expected, strategy);
    if (error) return showDialog('message', { type:'error', title:'Reversão não realizada', message:error });
    operationRef.current = operation; closeDialog(); setProgressKind('undo'); setUndoReturn(returnTo === 'historico' ? 'historico' : returnTo === 'propriedades' ? 'propriedades' : 'principal');
    setCurrentScreen('progresso'); setProgressValue(0); setProgressStatus('processing'); setProgressMessage('Preparando reversão simulada; originais preservados…');
    let value = 0;
    timerRef.current = setInterval(() => {
      if (operationRef.current !== operation) return;
      value += 20; setProgressValue(value);
      if (value === 40) setProgressMessage('Conferindo identidade, espaço e cópia temporária…');
      if (value === 60 && operation.scenario !== 'none') {
        stopProgressTimer(); operationRef.current = null;
        if (operation.scenario === 'restored' && !isFileLink(expected.type) && strategy === 'mover') {
          const result = applyUndo(demoRef.current, { expected, strategy:'mover', keepBackup:true, recordId:crypto.randomUUID() });
          result.record.status = 'erro: restauração concluída; origem preservada após falha de limpeza';
          result.record.metadata.recoveryRequired = true;
          demoRef.current = result.state; setDemo(result.state); setSelectedItem(null); setUndoReturn('principal');
          setProgressStatus('error'); setProgressMessage(`Arquivos restaurados em ${expected.dest}; o link foi removido. A origem ${expected.source} foi preservada porque a limpeza falhou. Confira os dois locais antes de qualquer nova operação. Não repita a reversão. Nenhum arquivo real foi alterado.`); return;
        }
        const message = isFileLink(expected.type) ? (operation.scenario === 'permission' ? 'Permissão negada ao remover o nome. O link e os dados foram preservados.' : 'A identidade do arquivo foi alterada. Nenhum nome foi removido; confira o acesso e atualize a lista.') : ({ copy:'Falha na cópia temporária; link e dados originais preservados.', changed:'A origem mudou durante a cópia; link e dados originais preservados. Atualize e confira os arquivos antes de tentar novamente.', cleanup:'Não foi possível limpar a área temporária. Operação não confirmada nesta demo; link e origem preservados para revisão.', space:'Espaço insuficiente para restaurar. Libere espaço e tente novamente.', restored:'Cenário de limpeza após restauração aplicável somente a mover arquivos de diretórios. Estado original preservado.' })[operation.scenario];
        setHistoryLog(prev => [historyRecord({ action:'Desfazer', link:expected, status:`erro: ${message}` }), ...prev]);
        setProgressStatus('error'); setProgressMessage(message); return;
      }
      if (value < 100) return;
      stopProgressTimer(); operationRef.current = null;
      try {
        const result = applyUndo(demoRef.current, { expected, strategy, keepBackup:operation.keepBackup, recordId:crypto.randomUUID() });
        demoRef.current = result.state; setDemo(result.state); setSelectedItem(null);
        setProgressStatus('success'); setProgressMessage(result.outcome.summary.join('\n'));
        setCurrentScreen(returnTo === 'historico' ? 'historico' : 'principal');
        showDialog('message', { type:'success', title:'Reversão Concluída', message:result.outcome.summary.join('\n') + '\n\nEstado atualizado na demonstração. Nenhum arquivo real foi alterado.' });
      } catch (error) { setProgressStatus('error'); setProgressMessage(error.message); }
    }, 450);
  };

  // ==========================================
  // BLOCOS DE RENDERIZAÇÃO (JSX Functions)
  // ==========================================

  const renderDialogOverlay = () => {
    if (!activeDialog) return null;

    return (
      <div onClick={event => { if (event.target === event.currentTarget && activeDialog === 'filter') closeDialog(); }} className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4 backdrop-blur-sm">
        <div ref={modalRef} role="dialog" aria-modal="true" aria-label={({ selector: 'Seletor de caminho', directory: 'Adicionar diretório de descoberta', about: 'Sobre WinLink', confirmCreate: 'Confirmar Criação de Link', confirmUndo: 'Confirmar reversão', filter: 'Filtros da lista', clearHistory: 'Limpar histórico', message: dialogConfig.title })[activeDialog]} tabIndex={-1} className="bg-white dark:bg-gray-900 rounded-xl shadow-2xl max-w-lg w-full border border-gray-200 dark:border-gray-700 flex flex-col max-h-[90vh] overflow-y-auto">

          {activeDialog === 'directory' && <div className="p-6 space-y-5"><div className="flex justify-between items-center"><h3 className="text-xl font-bold">Adicionar diretório de descoberta</h3><button className="button-secondary" onClick={closeDialog}>Cancelar</button></div><p className="text-sm text-gray-500">Seletor demonstrativo. Você também pode editar caminhos na lista de configurações.</p>{['C:/Users/Demo', 'D:/Projetos', 'E:/Arquivo'].map(path => <button className="button-secondary w-full justify-start" key={path} onClick={() => chooseDirectory(path)}><FolderOpen size={18} className="mr-2"/>{path}</button>)}</div>}
          {activeDialog === 'about' && <div className="p-6 space-y-5"><h3 className="text-xl font-bold">Sobre WinLink</h3><p>WinLink · versão 0.1.0 do aplicativo</p><p>Gerenciador de junções, links simbólicos e hard links para Windows. Protótipo navegável com dados fictícios; nenhuma operação real no disco.</p><h4 className="font-bold">Atalhos</h4><dl className="grid grid-cols-2 gap-3">{[['Ctrl+N','Criar novo'],['F5','Atualizar descoberta'],['Ctrl+,','Configurações'],['Ctrl+H','Histórico'],['Ctrl+F','Buscar'],['Ctrl+Q','Sair (demonstrativo)']].map(([key,text])=><React.Fragment key={key}><dt className="font-mono">{key}</dt><dd>{text}</dd></React.Fragment>)}</dl><button className="button-primary" onClick={closeDialog}>Fechar</button></div>}
          {/* Dialog: Selector (Seletor de Arquivos/Pastas 45-48) */}
          {activeDialog === 'selector' && (
            <>
              <div className="p-4 border-b border-gray-200 dark:border-gray-700 flex justify-between items-center bg-gray-50 dark:bg-gray-800 rounded-t-xl">
                <h3 className="font-bold flex items-center gap-2">
                  {dialogConfig.isDir ? <FolderOpen size={18}/> : <File size={18}/>}
                  {dialogConfig.setter === 'dest' ? 'Escolha o novo caminho do link' : `Selecione ${dialogConfig.isDir ? 'a Pasta' : 'o Arquivo existente'}`}
                </h3>
                <button aria-label="Fechar seletor" onClick={closeDialog} className="text-gray-500 hover:text-gray-800 dark:hover:text-white"><X size={20}/></button>
              </div>
              <div className="p-4 flex-1 overflow-auto">
                <p className="text-sm text-gray-500 mb-4">Simulação da janela nativa do Windows.</p>
                <div className="space-y-2 font-mono text-sm">
                  {(dialogConfig.isDir ? (dialogConfig.setter === 'dest' ? ['C:\\Links\\NovoProjeto', 'D:\\Links\\NovoProjeto'] : ['C:\\Projetos', 'D:\\Dados']) : (dialogConfig.setter === 'dest' ? ['C:\\Links\\novo-arquivo.txt', 'D:\\Links\\novo-arquivo.txt'] : ['C:\\Dados\\arquivo.txt', 'D:\\Dados\\arquivo.txt'])).map(p => (
                    <button key={p} onClick={() => handleSelectorPick(p)} className="w-full text-left p-2 hover:bg-blue-50 dark:hover:bg-blue-900/30 rounded border border-transparent hover:border-blue-200 dark:hover:border-blue-800">
                      {p}
                    </button>
                  ))}
                </div>
              </div>
            </>
          )}

          {/* Dialog: Confirm Create (Prévia Final 13-16) */}
          {activeDialog === 'confirmCreate' && (
            <>
              <div className="p-4 border-b border-gray-200 dark:border-gray-700 bg-blue-50 dark:bg-blue-900/20 rounded-t-xl">
                <h3 className="font-bold text-blue-800 dark:text-blue-300 text-lg">Confirmar Criação de Link</h3>
              </div>
              <div className="p-6 space-y-4">
                <p className="text-sm">O sistema executará a seguinte ação estrutural:</p>
                <div className="p-3 bg-gray-100 dark:bg-gray-800 rounded border border-gray-300 dark:border-gray-600 text-sm">
                  <div><strong>Destino (Ponto de Acesso):</strong> {dialogConfig.dest}</div>
                  <div className="my-1 text-center text-gray-400">apontará para</div>
                  <div><strong>Origem (Alvo Físico):</strong> {dialogConfig.source}</div>
                </div>
                <p className="text-sm font-bold">Tipo: {dialogConfig.type}</p>
                <div className="p-4 rounded border border-blue-200 dark:border-blue-800 bg-blue-50 dark:bg-blue-900/20 text-sm space-y-3">
                  {isFileLink(dialogConfig.type) ? <>
                    <p>O arquivo existente será preservado. Um novo nome de acesso será criado no caminho do link; nenhum arquivo existente será substituído.</p>
                    {dialogConfig.type === 'Hardlink' ? <p>Os dois nomes equivalem ao mesmo arquivo, no mesmo volume. Alterações por qualquer nome afetam os mesmos dados; não há uma cópia independente.</p> : <p>O link simbólico apontará para o arquivo existente. A criação pode exigir Modo de Desenvolvedor ou permissões apropriadas.</p>}
                  </> : <>
                    {dialogConfig.targetKind === 'directory' ? <ol className="list-decimal pl-5 space-y-2"><li>{dialogConfig.sourceExists ? 'Usar a pasta no local dos dados.' : 'Criar a pasta no local dos dados.'}</li><li>Copiar os arquivos de <strong className="break-all">{dialogConfig.dest}</strong> para <strong className="break-all">{dialogConfig.source}</strong>, preservando o conteúdo anterior.</li><li>Após conferir a cópia, preservar a pasta original como backup temporário e criar o link no lugar dela.</li><li>Conferir a criação antes de limpar o backup. Se houver falha, preservar os originais e informar onde os dados ficaram.</li></ol> : <p>{dialogConfig.sourceExists ? 'Preservar a pasta e os dados existentes no local de origem.' : 'Criar uma pasta vazia no local dos dados.'} Depois, criar o novo caminho de acesso apontando para essa pasta.</p>}
                    <p>Nenhum conflito de nomes será sobrescrito automaticamente. Em caso de falha na migração, o destino original deve ser preservado.</p>
                  </>}
                </div>
                <section className="p-4 rounded-lg border border-gray-200 dark:border-gray-700 space-y-3" aria-live="polite"><h4 className="font-bold">Conferência antes de criar</h4>{dialogConfig.previewScenario === 'calculating' ? <><p role="status">Calculando tamanho e espaço disponível…</p><button className="button-secondary" onClick={() => setDialogConfig(c => ({ ...c, previewScenario:'normal' }))}>Concluir cálculo simulado</button></> : <><dl className="grid grid-cols-2 gap-2 text-sm"><dt>Espaço necessário</dt><dd>{dialogConfig.targetKind === 'directory' ? '42 MiB' : 'Sem cópia de dados'}</dd><dt>Espaço disponível</dt><dd>{dialogConfig.previewScenario === 'space' ? '8 MiB' : '120 GiB'} (exemplo)</dd></dl>{dialogConfig.previewScenario === 'space' && <p role="alert" className="text-red-600 dark:text-red-400">Espaço insuficiente. Confirmação bloqueada. Revise o cenário após liberar espaço.</p>}{dialogConfig.previewScenario === 'nested' && <div className="notice-warning"><p className="font-bold">Links aninhados encontrados</p><p className="break-all">{dialogConfig.source}/Dependencias → D:/Bibliotecas</p><p>O redirecionamento pode causar confusão. Considere usar o link original diretamente.</p></div>}{dialogConfig.previewScenario === 'processes' && <div className="notice-warning"><p className="font-bold">Feche os processos antes de continuar</p><ul><li>Code.exe · PID 4260 (exemplo)</li><li>Explorer.exe · PID 1820 (exemplo)</li></ul><p>Feche manualmente os arquivos em uso e recalcule a prévia. Nenhum processo será encerrado pela demo.</p><button className="button-secondary mt-2" onClick={() => setDialogConfig(c=>({...c,previewScenario:'normal'}))}>Simular processos liberados</button></div>}</>}</section>
                <p className="text-xs text-gray-500">Confirmação de uma simulação: nenhum arquivo ou link real será criado, copiado ou removido.</p>
                <div className="pt-4 flex justify-end gap-3">
                  <button onClick={closeDialog} className="px-4 py-2 border rounded hover:bg-gray-50 dark:border-gray-600 dark:hover:bg-gray-800">Revisar</button>
                  <button disabled={['space', 'calculating', 'processes'].includes(dialogConfig.previewScenario)} onClick={executeCreation} className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700">Confirmar e Iniciar</button>
                </div>
              </div>
            </>
          )}

          {/* Dialog: Confirm Undo — the reviewed snapshot is bound to a live link id. */}
          {activeDialog === 'confirmUndo' && dialogConfig.item && (
            <>
              <div className="p-4 border-b border-amber-200 dark:border-amber-700 bg-amber-50 dark:bg-amber-900/20 rounded-t-xl">
                <h3 className="font-bold text-amber-900 dark:text-amber-300 flex items-center gap-2"><ShieldAlert size={20}/>{isFileLink(dialogConfig.item.type) ? 'Remover nome de arquivo' : 'Estratégia de Reversão'}</h3>
              </div>
              <div className="p-6 space-y-5">
                <label className="block text-sm">Cenário da reversão<select className="w-full" value={undoScenario} onChange={e=>{ setUndoScenario(e.target.value); if (e.target.value === 'restored') setKeepBackup(false); }}><option value="none">Sucesso</option>{isFileLink(dialogConfig.item.type) ? <><option value="permission">Permissão negada ao remover nome</option><option value="changed">Identidade alterada após confirmar</option></> : <><option value="copy">Falha de cópia, originais preservados</option><option value="changed">Origem alterada durante a cópia</option><option value="cleanup">Falha na limpeza temporária</option><option value="space">Espaço insuficiente</option></>}{!isFileLink(dialogConfig.item.type) && undoStrategy === 'mover' && <option value="restored">Restaurado com origem preservada após falha de limpeza</option>}</select></label>
                <dl className="space-y-3 text-sm"><div><dt className="font-bold">Caminho do link selecionado</dt><dd className="font-mono break-all mt-1">{dialogConfig.item.dest}</dd></div><div><dt className="font-bold">{dialogConfig.item.type === 'Hardlink' ? 'Outro nome do mesmo arquivo' : 'Local dos dados'}</dt><dd className="font-mono break-all mt-1">{dialogConfig.item.source}</dd></div></dl>
                {isFileLink(dialogConfig.item.type) ? <p className="text-sm">Será removido somente o nome selecionado. Os outros nomes e seus dados não serão alterados. Nenhuma pasta vazia será criada.</p> : <fieldset className="space-y-3"><legend className="mb-2 font-bold text-sm">O que fazer com os arquivos?</legend>{[['mover', 'Mover arquivos de volta'], ['duplicar', 'Duplicar'], ['remover', 'Remover apenas o link']].map(([value, label]) => <label key={value} className={`block p-3 border rounded-lg ${dialogConfig.item.status !== 'Ativo' && value !== 'remover' ? 'opacity-50' : 'cursor-pointer'} ${undoStrategy === value ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20' : 'border-gray-300 dark:border-gray-600'}`}><span className="flex items-center gap-2 font-bold text-sm"><input type="radio" name="undoStrat" value={value} checked={undoStrategy === value} disabled={dialogConfig.item.status !== 'Ativo' && value !== 'remover'} onChange={() => { setUndoStrategy(value); if (undoScenario === 'restored') setUndoScenario('none'); }}/>{label}</span></label>)}</fieldset>}
                {!isFileLink(dialogConfig.item.type) && undoStrategy === 'mover' && <label className="flex items-start gap-2 text-sm"><input type="checkbox" checked={keepBackup} onChange={e => { setKeepBackup(e.target.checked); if (e.target.checked && undoScenario === 'restored') setUndoScenario('none'); }}/>Manter os dados na origem como backup após mover</label>}
                {dialogConfig.item.status !== 'Ativo' && <p className="p-3 text-sm rounded border border-amber-200 dark:border-amber-800 bg-amber-50 dark:bg-amber-900/20">A origem não está disponível para restauração. Apenas a remoção do nome/link está disponível.</p>}
                <div className="p-4 border border-amber-200 dark:border-amber-800 bg-amber-50 dark:bg-amber-900/20 rounded-lg text-sm"><h4 className="font-bold mb-2">Resultado após confirmar</h4><ul className="list-disc pl-5 space-y-2 break-words">{(isFileLink(dialogConfig.item.type) && dialogConfig.item.status !== 'Ativo' ? [`Remover somente o nome ${dialogConfig.item.dest}.`, 'Os outros nomes e dados não serão alterados. O acesso à origem deve ser verificado.'] : undoSummary(dialogConfig.item, isFileLink(dialogConfig.item.type) ? 'remover' : undoStrategy, keepBackup)).map(text => <li key={text}>{text}</li>)}</ul></div>
                <div className="pt-2 flex flex-wrap justify-end gap-3"><button onClick={closeDialog} className="px-4 py-2 border rounded dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-800">Cancelar</button><button onClick={executeUndo} className="px-4 py-2 rounded bg-red-600 hover:bg-red-700 text-white font-bold">Executar Reversão</button></div>
              </div>
            </>
          )}

          {activeDialog === 'filter' && <div className="p-6 space-y-5">
            <div className="flex items-center justify-between gap-4"><h3 className="text-xl font-bold">Filtros da lista</h3><button aria-label="Fechar filtros" onClick={closeDialog} className="p-2 rounded-md hover:bg-gray-100 dark:hover:bg-gray-800"><X size={20}/></button></div>
            <label className="block">Tipo<select value={filterDraft.type} onChange={e => setFilterDraft({ ...filterDraft, type: e.target.value })} className="w-full"><option value="">Todos</option>{['Junction', 'Symlink (Dir)', 'Symlink (File)', 'Hardlink'].map(t => <option key={t}>{t}</option>)}</select></label>
            <label className="block">Status<select value={filterDraft.status} onChange={e => setFilterDraft({ ...filterDraft, status: e.target.value })} className="w-full"><option value="">Todos</option><option>Ativo</option><option>Quebrado</option><option>Inacessível</option></select></label>
            <label className="block">Criador<select className="w-full" value={filterDraft.creator || ''} onChange={e => setFilterDraft({ ...filterDraft, creator:e.target.value })}><option value="">Todos</option><option>App</option><option>Existente</option><option>Manual</option></select></label>
            <div className="flex flex-wrap justify-end gap-3 pt-4 border-t border-gray-200 dark:border-gray-700"><button className="button-secondary mr-auto" onClick={() => setFilterDraft({ type: '', status: '', creator: '' })}>Limpar filtros</button><button className="button-secondary" onClick={closeDialog}>Cancelar</button><button className="button-primary" onClick={() => { setLinkFilter({ ...filterDraft }); closeDialog(); }}>Aplicar filtros</button></div>
          </div>}
          {activeDialog === 'clearHistory' && <div className="p-6 space-y-4"><h3 className="text-xl font-bold">Limpar histórico?</h3><p>Excluir os {historyLog.length} registros fictícios da sessão? Os links permanecem na lista e podem ser revertidos pelas propriedades. Esta ação não pode ser desfeita.</p><button className="button-secondary" onClick={closeDialog}>Cancelar</button><button className="button-danger" onClick={() => { clearHistory(); }}>Confirmar limpeza</button></div>}
          {/* Dialog: Generic Message (Erros e Confirmações 36-44) */}
          {activeDialog === 'message' && (
             <div className="p-6 text-center space-y-4">
                <div className="flex justify-center mb-2">
                  {dialogConfig.type === 'error' ? <XCircle size={48} className="text-red-500"/> : dialogConfig.type === 'warning' ? <AlertTriangle size={48} className="text-amber-500"/> : <CheckCircle size={48} className="text-green-500"/>}
                </div>
                <h3 className="text-xl font-bold">{dialogConfig.title}</h3>
                <p className="text-gray-600 dark:text-gray-300 whitespace-pre-line">{dialogConfig.message}</p>
                <div className="pt-4">
                  <button onClick={closeDialog} className="px-6 py-2 bg-gray-200 dark:bg-gray-700 rounded-lg hover:bg-gray-300 font-medium">OK, Fechar</button>
                </div>
             </div>
          )}

        </div>
      </div>
    );
  };

  const renderPrincipal = () => {
    const filteredLinks = sortedLinks(links, sort, sortDirection).filter(l => (!linkFilter.creator || l.creator === linkFilter.creator) && (!linkFilter.type || l.type === linkFilter.type) && (!linkFilter.status || l.status === linkFilter.status) && [l.name, l.source, l.dest].some(v => v.toLowerCase().includes(searchQuery.toLowerCase())));

    return (
      <div className="screen-content flex-1 min-w-0 min-h-0 p-6 overflow-auto focus:outline-none" tabIndex={0}>
        <div className="flex flex-wrap gap-3 justify-between items-center mb-6">
          <h2 className="text-2xl font-bold">Meus Links</h2><button className="button-secondary" disabled={principalViewMode === 'scanning'} onClick={() => setPrincipalViewMode('scanning')}>Atualizar <span className="ml-2 text-xs opacity-60">F5</span></button><button className="button-secondary" onClick={() => { setSearchQuery(''); setLinkFilter({ type:'', status:'', creator:'' }); setPrincipalViewMode('scanning'); }}>Início</button>
          <div className="flex flex-wrap gap-2">
            <select
              aria-label="Modo de visualização" value={principalViewMode} onChange={(e) => setPrincipalViewMode(e.target.value)}
              className="px-2 border rounded-md dark:bg-gray-700 dark:border-gray-600 text-sm focus:ring-2 focus:ring-blue-500"
            >
              <option value="normal">Visão Normal</option>
              <option value="compact">Compacta</option>

            </select>
            <div className="relative">
              <Search className="absolute left-3 top-2.5 text-gray-400" size={18} />
              <input
                type="text"
                aria-label="Buscar links" placeholder="Buscar (Ex: hosts)..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10 pr-4 py-2 w-56 rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <button onClick={() => showDialog('filter')} className="flex items-center gap-2 px-4 py-2 bg-white dark:bg-gray-700 rounded-md border border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-600">
              <Filter size={18} /> Filtros
            </button>
          </div>
        </div>

        <div className="flex flex-wrap gap-3 items-end mb-6"><label className="text-sm">Ordenar por<select value={sort} onChange={e => setSort(e.target.value)}>{[['source','Origem'],['dest','Destino'],['creator','Criador'],['type','Tipo'],['size','Tamanho'],['status','Status']].map(([value,label])=><option key={value} value={value}>{label}</option>)}</select></label><label className="text-sm">Ordem<select value={sortDirection} onChange={e => setSortDirection(e.target.value)}><option value="asc">Crescente</option><option value="desc">Decrescente</option></select></label></div>
        <p role="status" className="text-sm text-gray-500 dark:text-gray-400 mb-4">{initialCache === 'ready' ? lastScan : 'Cache fictício inicial carregado; atualizando descoberta…'}</p>
        <button className="button-secondary mb-4" onClick={() => { setInitialCache('loading'); setPrincipalViewMode('scanning'); }}>Simular abertura com cache</button>
        <p className="text-sm mb-3">{filteredLinks.length} de {links.length} links · {linkFilter.type || 'Todos os tipos'} · {linkFilter.status || 'Todos os status'} · {linkFilter.creator || 'Todos os criadores'}</p><label className="block text-sm mb-6">Cenário da atualização <select value={cacheScenario} onChange={e => setCacheScenario(e.target.value)}><option value="success">Sucesso</option><option value="failure">Origem inacessível</option></select></label>{cacheError && <div role="alert" className="p-3 mb-3 border rounded">Não foi possível atualizar as origens fictícias. Último cache preservado. <button className="button-secondary" onClick={() => setPrincipalViewMode('scanning')}>Tentar novamente</button></div>}
        {principalViewMode === 'scanning' && initialCache !== 'loading' ? (
           <div className="flex-1 flex flex-col items-center justify-center space-y-4">
             <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
             <p className="text-gray-500 font-medium">Sincronizando cache de sistema...</p>
           </div>
        ) : filteredLinks.length === 0 ? (
          <div className="flex flex-col items-center justify-center flex-1 space-y-4">
            <div className="w-20 h-20 bg-gray-100 dark:bg-gray-700 rounded-full flex items-center justify-center">
              <Search size={32} className="text-gray-400" />
            </div>
            <h3 className="text-xl font-medium">{links.length === 0 ? 'Nenhum link configurado' : 'Busca sem resultados'}</h3>
            <p className="text-gray-500 dark:text-gray-400">Verifique os filtros ou inicie a criação.</p>
          </div>
        ) : (
          <div className="grid gap-4">
            {filteredLinks.map(link => (
              <div
                key={link.id} data-testid={`link-card-${link.id}`}
                className={`flex flex-col sm:flex-row sm:items-center justify-between p-4 border rounded-lg bg-gray-50 dark:bg-gray-800 border-gray-200 dark:border-gray-700 hover:shadow-md hover:border-blue-300 dark:hover:border-blue-600 transition-all ${principalViewMode === 'compact' ? 'py-2' : ''}`}
              >
                <div className="flex items-center gap-4 flex-1 min-w-0">
                  <div className={`p-3 rounded-xl flex-shrink-0 ${link.type === 'Hardlink' ? 'bg-purple-100 text-purple-600 dark:bg-purple-900/30 dark:text-purple-400' : 'bg-blue-100 text-blue-600 dark:bg-blue-900/30 dark:text-blue-400'}`}>
                    {link.type.includes('Dir') || link.type === 'Junction' ? <Folder size={24} /> : <File size={24} />}
                  </div>
                  <div className="flex flex-col overflow-hidden w-full pr-4">
                    <h4 className="font-semibold text-lg break-all">{link.name}</h4><p className="text-xs text-gray-500 dark:text-gray-400">{link.creator} · {formatSize(link.size)} {link.size != null && '(exemplo)'}</p>
                    <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400 mt-1">
                      <span className="truncate" title={link.source}>{link.source}</span>
                      <ArrowRight size={14} className="flex-shrink-0 text-gray-400" />
                      <span className="truncate font-medium text-gray-800 dark:text-gray-200" title={link.dest}>{link.dest}</span>
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-6 flex-shrink-0">
                  <div className="flex flex-col items-end">
                    <span className="text-xs font-bold uppercase tracking-wider text-gray-500">{link.type}</span>
                    <span className={`text-sm flex items-center gap-1 mt-1 font-medium ${link.status === 'Ativo' ? 'text-emerald-600 dark:text-emerald-400' : 'text-red-600 dark:text-red-400'}`}>
                      {link.status === 'Ativo' ? <CheckCircle size={14} /> : <XCircle size={14} />} {link.status}
                    </span>
                  </div>
                  <button
                    onClick={() => { setSelectedItem(link); setStatsMode('loading'); setFolderScenario('available'); setCurrentScreen('propriedades'); }}
                    className="p-2 text-gray-400 hover:text-blue-600 dark:hover:text-blue-400 rounded-md hover:bg-blue-50 dark:hover:bg-blue-900/30 transition-colors focus:ring-2 focus:ring-blue-500"
                    title="Propriedades e Ações"
                  >
                    <MoreVertical size={20} />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    );
  };

  const renderCriar = () => (
    <div className="screen-content flex-1 min-w-0 min-h-0 p-6 overflow-auto">
      <div className="flex justify-between mb-6">
        <h2 className="text-2xl font-bold">Criar Novo Link</h2>
        <div className="flex items-center gap-2 text-sm">
           <span className="text-gray-500">Cenário da operação:</span>
           <select aria-label="Cenário de operação" value={simulateErrorType} onChange={e => setSimulateErrorType(e.target.value)} className="p-1 border rounded dark:bg-gray-800 dark:border-gray-600">
             <option value="none">Nenhum (Sucesso)</option>
             <option value="occupied">Destino Ocupado</option>
             <option value="permission">Permissão Negada</option><option value="space">Espaço insuficiente</option><option value="unavailable">Origem indisponível</option><option value="backup">Sucesso com backup preservado</option><option value="history">Sucesso com falha no histórico</option>
           </select>
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-8">
        <div className="space-y-6">
          <div className="space-y-3">
            <label className="font-bold text-sm text-gray-700 dark:text-gray-300">Tipo de Estrutura</label>
            <div className="grid grid-cols-2 gap-3">
              {[
                {id: 'Junction', desc: 'Atalho de pasta local (Padrão).'},
                {id: 'Symlink (Dir)', desc: 'Pasta local ou de rede. Pode exigir permissões especiais.'},
                {id: 'Symlink (File)', desc: 'Atalho avançado de arquivo.'},
                {id: 'Hardlink', desc: 'Nomes equivalentes para o mesmo arquivo (Mesmo Volume).'}
              ].map((t) => (
                <button
                  key={t.id} onClick={() => { setLinkType(t.id); setSourceEntry(isFileLink(t.id) ? 'file' : 'directory'); setCreationErrors([]); }}
                  className={`p-3 border rounded-lg text-left transition-all focus:outline-none focus:ring-2 focus:ring-blue-500 ${linkType === t.id ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20 ring-1 ring-blue-500' : 'border-gray-300 dark:border-gray-600 hover:border-gray-400'}`}
                >
                  <div className="font-bold text-gray-800 dark:text-gray-100">{t.id}</div>
                  <div className="text-xs text-gray-500 mt-1">{t.desc}</div>
                </button>
              ))}
            </div>
          </div>

          <div className="space-y-2">
            <label htmlFor="creation-source" className="font-bold text-sm text-gray-700 dark:text-gray-300 flex items-center gap-2">
              1. Local dos dados (Origem) <Info size={14} className="text-blue-500" title="Local onde os arquivos reais estão gravados no disco."/>
            </label>
            <div className="flex flex-wrap gap-2">
              <input
                id="creation-source" type="text" value={sourcePath} onChange={(e) => setSourcePath(e.target.value)}
                className="flex-1 p-2.5 border rounded-lg bg-white dark:bg-gray-900 border-gray-300 dark:border-gray-600 focus:ring-2 focus:ring-blue-500 outline-none font-mono text-sm"
                placeholder={linkType.includes('File') || linkType === 'Hardlink' ? "C:\\Original\\arquivo.txt" : "C:\\Original\\Pasta"}
              />
              <button onClick={() => openSelector('source')} className="px-4 bg-gray-100 dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 font-medium">Procurar</button>
            </div>
          </div>

          <div className="space-y-2">
            <label htmlFor="creation-dest" className="font-bold text-sm text-gray-700 dark:text-gray-300 flex items-center gap-2">
              2. Caminho do novo link (Destino) <Info size={14} className="text-blue-500" title="Onde o novo atalho/nome será criado."/>
            </label>
            <div className="flex flex-wrap gap-2">
              <input
                id="creation-dest" type="text" value={destPath} onChange={(e) => setDestPath(e.target.value)}
                className="flex-1 p-2.5 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-900 focus:ring-2 focus:ring-blue-500 outline-none font-mono text-sm"
                placeholder="D:\\Atalhos\\NovoNome"
              />
              <button onClick={() => openSelector('dest')} className="px-4 bg-gray-100 dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 font-medium">Procurar</button>
            </div>
          </div>

          <label className="block text-sm font-medium">Cenário da prévia<select value={previewScenario} onChange={e => setPreviewScenario(e.target.value)} className="w-full"><option value="normal">Condições normais</option><option value="space">Espaço insuficiente na prévia</option><option value="nested">Links aninhados</option><option value="processes">Arquivos em uso por processos</option><option value="calculating">Calculando informações</option></select></label>
          <fieldset className="space-y-4 p-4 border border-dashed border-gray-300 dark:border-gray-600 rounded-lg text-sm">
            <legend className="px-2 font-bold text-gray-600 dark:text-gray-300">Cenário da demonstração</legend>
            <p className="text-xs text-gray-500 dark:text-gray-400">Informe o que existe nesses caminhos fictícios. Esta demo não consulta arquivos do computador. Caminhos já usados na sessão refletem o resultado das operações simuladas.</p>
            <label className="block space-y-1">
              <span className="font-medium">O que existe no local dos dados?</span>
              <select aria-label="Estado do local dos dados" value={demo.paths[normalizePath(sourcePath)]?.kind || sourceEntry} disabled={Boolean(demo.paths[normalizePath(sourcePath)])} onChange={e => setSourceEntry(e.target.value)} className="block w-full p-2 border rounded dark:bg-gray-900 dark:border-gray-600">
                <option value="directory">Uma pasta existente</option><option value="file">Um arquivo existente</option><option value="missing">Ainda não existe</option>
              </select>
            </label>
            <label className="block space-y-1">
              <span className="font-medium">O que existe no caminho do novo link?</span>
              <select aria-label="Estado do caminho do link" value={demo.paths[normalizePath(destPath)]?.kind || targetEntry} disabled={Boolean(demo.paths[normalizePath(destPath)])} onChange={e => setTargetEntry(e.target.value)} className="block w-full p-2 border rounded dark:bg-gray-900 dark:border-gray-600">
                <option value="missing">Ainda não existe</option><option value="directory">Uma pasta com arquivos</option><option value="file">Um arquivo</option><option value="link">Já é um link</option>
              </select>
            </label>
            {!isFileLink(linkType) && creationSnapshot().targetKind === 'directory' && creationSnapshot().sourceKind === 'directory' && <label className="flex items-start gap-2"><input type="checkbox" checked={copyConflicts} onChange={e => setCopyConflicts(e.target.checked)}/>Há arquivos com o mesmo nome nas duas pastas</label>}
            <p className="text-xs text-gray-500 dark:text-gray-400">{isFileLink(linkType) ? 'É necessário um arquivo existente e um novo nome livre. Hard links precisam estar no mesmo volume.' : 'Uma pasta anterior no caminho do link será migrada com preservação dos arquivos. Um link existente não será substituído.'}</p>
          </fieldset>
          {creationErrors.length > 0 && <div role="alert" className="p-4 border border-red-200 dark:border-red-800 bg-red-50 dark:bg-red-900/20 text-red-800 dark:text-red-300 rounded-lg text-sm"><p className="font-bold mb-2">Corrija antes de continuar:</p><ul className="list-disc pl-5 space-y-1">{creationErrors.map(error => <li key={error}>{error}</li>)}</ul></div>}
          <div className="pt-4">
            <button onClick={handleCreateConfirm} className="w-full py-3 rounded-lg font-bold text-white bg-blue-600 hover:bg-blue-700 shadow-md focus:outline-none focus:ring-4 focus:ring-blue-300 transition-all">
              Avançar
            </button>
          </div>
        </div>

        <div className="border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50 rounded-xl p-6 flex flex-col">
          <h3 className="text-lg font-bold mb-4 flex items-center gap-2 border-b border-gray-200 dark:border-gray-700 pb-2">
            Prévia Estrutural (Visualização)
          </h3>

          <div className="space-y-6 flex-1 flex flex-col justify-center">
            <div className="relative flex-1 flex flex-col justify-center items-center py-4">
              <div className="w-full flex justify-between items-center px-2 relative z-10">
                <div className="text-center w-5/12 bg-white dark:bg-gray-800 p-4 rounded-xl shadow-sm border-2 border-blue-200 dark:border-blue-800">
                  <div className="text-xs text-blue-600 dark:text-blue-400 font-bold uppercase tracking-wider mb-2">Ponto de Acesso</div>
                  <div className="w-12 h-12 bg-blue-50 dark:bg-blue-900/30 text-blue-600 rounded-lg flex items-center justify-center mx-auto mb-3">
                    <LinkIcon size={24}/>
                  </div>
                  <div className="text-xs font-mono break-all text-gray-800 dark:text-gray-200 min-h-8">{destPath || '[Destino Vazio]'}</div>
                </div>

                <div className="flex-1 flex justify-center text-blue-400">
                  <ArrowRight size={32} />
                </div>

                <div className="text-center w-5/12 bg-gray-100 dark:bg-gray-700 p-4 rounded-xl border border-gray-300 dark:border-gray-600">
                  <div className="text-xs text-gray-500 dark:text-gray-400 font-bold uppercase tracking-wider mb-2">Dados Físicos</div>
                  <div className="w-12 h-12 bg-white dark:bg-gray-800 text-gray-600 dark:text-gray-300 rounded-lg flex items-center justify-center mx-auto mb-3 shadow-sm">
                    {linkType.includes('File') || linkType === 'Hardlink' ? <File size={24}/> : <Folder size={24}/>}
                  </div>
                  <div className="text-xs font-mono break-all text-gray-800 dark:text-gray-200 min-h-8">{sourcePath || '[Origem Vazia]'}</div>
                </div>
              </div>
              <div className="absolute top-1/2 -translate-y-1/2 w-full px-20 -z-0">
                 <div className="border-t-2 border-dashed border-blue-300 dark:border-blue-700"></div>
              </div>
            </div>

            <div className="p-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-100 dark:border-blue-800 rounded-lg text-sm text-gray-800 dark:text-gray-200">
              <span className="font-bold">Interpretação: </span>
              {linkType === 'Hardlink' ? 'Os dois nomes representam o mesmo arquivo, no mesmo volume. Modificar um altera os mesmos dados.' : creationSnapshot().targetKind === 'directory' ? `Os arquivos da pasta em ${destPath || '[caminho do link]'} serão copiados para ${sourcePath || '[local dos dados]'} antes de criar o link. A confirmação mostrará as etapas de preservação.` : creationSnapshot().sourceKind === 'missing' ? 'Para diretórios, será criada uma pasta vazia no local dos dados e um link apontando para ela. Para arquivos, escolha uma origem existente.' : `O novo caminho ${destPath || '[caminho do link]'} permitirá acessar o conteúdo em ${sourcePath || '[local dos dados]'}.`}
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  const renderProgresso = () => (
    <div className="screen-content flex-1 min-w-0 min-h-0 p-6 overflow-auto bg-gray-50 dark:bg-gray-900/50">
      <div className="w-full max-w-lg mx-auto bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl p-8 shadow-2xl">
        <h3 className="text-xl font-bold mb-6 text-center border-b border-gray-100 dark:border-gray-700 pb-4">
          {progressStatus === 'processing' ? progressKind === 'undo' ? 'Reversão em Andamento' : 'Operação em Andamento' : 'Status da Operação'}
        </h3>

        {progressStatus === 'success' && (
          <div className="flex flex-col items-center py-4 text-center">
            <CheckCircle size={64} className="text-emerald-500 mb-4" />
            <h4 className="text-xl font-bold mb-2">Criação Bem-sucedida</h4>
            <p className="text-gray-600 dark:text-gray-400 mb-6">{progressMessage}</p>
            <div className="flex gap-3 w-full">
              <button onClick={() => setCurrentScreen('principal')} className="flex-1 py-2.5 bg-gray-100 dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-200 font-medium">Ir para Lista</button>
              <button onClick={resetCreation} className="flex-1 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium">Criar Outro</button>
            </div>
          </div>
        )}

        {(progressStatus === 'error' || progressStatus === 'cancelled') && (
           <div className="flex flex-col items-center py-4 text-center">
            <XCircle size={64} className="text-red-500 mb-4" />
            <h4 className="text-xl font-bold mb-2">{progressStatus === 'cancelled' ? 'Cancelado' : 'Falha na Operação'}</h4>
            <div className="p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded text-red-700 dark:text-red-400 text-sm mb-6 w-full text-left font-mono">
              {progressStatus === 'cancelled' ? '[CANCELADO]' : '[FALHA]'}: {progressMessage}
            </div>
            <button onClick={resetCreation} className="px-6 py-2.5 bg-gray-100 dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-200 font-medium">{progressKind === 'undo' ? 'Voltar à seleção' : 'Voltar para Edição'}</button>
          </div>
        )}

        {progressStatus === 'cancelling' && <p role="status">{progressMessage}</p>}
        {progressStatus === 'processing' && (
          <div className="py-2">
            <div className="mb-2 flex justify-between text-sm font-bold">
              <span>{progressMessage}</span>
              <span className="text-blue-600 dark:text-blue-400">{progressValue}%</span>
            </div>
            <div role="progressbar" aria-label="Progresso da operação" aria-valuenow={progressValue} aria-valuemin={0} aria-valuemax={100} className="w-full h-4 bg-gray-100 dark:bg-gray-700 rounded-full overflow-hidden mb-6 border border-gray-200 dark:border-gray-600">
              <div className="h-full bg-blue-600 transition-all duration-300 ease-out" style={{ width: `${progressValue}%` }}></div>
            </div>
            <div className="flex justify-end">
              <button onClick={handleCancelProgress} className="px-6 py-2 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-red-50 dark:hover:bg-red-900/20 hover:text-red-600 dark:hover:border-red-300 transition-colors font-medium">
                Interromper
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );

  const renderHistorico = () => (
    <div className="screen-content flex-1 min-w-0 min-h-0 p-6 overflow-auto">
      <div className="flex flex-wrap gap-3 justify-between items-center mb-6">
        <div>
          <h2 className="text-2xl font-bold">Histórico de Operações</h2>
          <p className="text-sm text-gray-500">Registro de criações e reversões. Clique em "Desfazer" para reverter o estado.</p>
        </div>
        <div className="flex flex-wrap gap-2">
           <button onClick={exportHistory} className="flex items-center gap-2 px-4 py-2 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-md hover:bg-gray-50">
            <Download size={16}/> Exportar
          </button>
          <button onClick={() => showDialog('clearHistory')} className="flex items-center gap-2 px-4 py-2 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-md hover:bg-red-50 hover:text-red-600 hover:border-red-300">
            <Trash2 size={16}/> Limpar
          </button>
        </div>
      </div>

      <button className="button-secondary mb-4" onClick={loadHistoryExamples}>Carregar exemplos dos tipos de operação</button><label className="block text-sm mb-5">Cenário do histórico<select value={historyScenario} onChange={e=>setHistoryScenario(e.target.value)}><option value="normal">Normal</option><option value="clear">Falha ao limpar</option><option value="export">Falha ao exportar</option></select></label><fieldset className="history-filters mb-4"><legend className="font-semibold mb-3">Filtrar histórico</legend><label>Operação<select value={historyFilter.operation || ''} onChange={e=>setHistoryFilter({...historyFilter,operation:e.target.value})}><option value="">Todas</option>{OPERATIONS.map(op=><option key={op}>{op}</option>)}</select></label><label>Período<select value={historyFilter.period || 'all'} onChange={e=>setHistoryFilter({...historyFilter,period:e.target.value,...dateRange(e.target.value)})}><option value="all">Todos</option><option value="today">Hoje</option><option value="week">Última semana</option><option value="month">Último mês</option><option value="custom">Personalizado</option></select></label><label>Tipo de link<select value={historyFilter.type} onChange={e => setHistoryFilter({ ...historyFilter, type: e.target.value })}><option value="">Todos</option>{['Junction', 'Symlink (Dir)', 'Symlink (File)', 'Hardlink'].map(t => <option key={t}>{t}</option>)}</select></label><label>Resultado<select value={historyFilter.result} onChange={e => setHistoryFilter({ ...historyFilter, result: e.target.value })}><option value="">Todos</option><option value="sucesso">Sucesso</option><option value="erro">Falha</option><option value="cancelado">Cancelado</option></select></label><label>De<input type="date" value={historyFilter.from} onChange={e => setHistoryFilter({ ...historyFilter, from: e.target.value, period:'custom' })}/></label><label>Até<input type="date" min={historyFilter.from} value={historyFilter.to} onChange={e => setHistoryFilter({ ...historyFilter, to: e.target.value, period:'custom' })}/></label><button className="button-secondary" onClick={() => setHistoryFilter({ type: '', result: '', from: '', to: '', operation: '', period: 'all' })}>Limpar filtros</button>{historyFilter.to && historyFilter.from > historyFilter.to && <p role="alert">O fim do período deve ser posterior ao início.</p>}</fieldset>
      <p className="text-sm mb-4" role="status">Total: {filterHistory(historyLog, historyFilter).length} de {historyLog.length} operações</p><div className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-xl overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="bg-gray-50 dark:bg-gray-800 text-gray-700 dark:text-gray-300 border-b border-gray-200 dark:border-gray-700 sticky top-0">
              <tr>
                <th className="p-4 font-bold">Ação Realizada</th>
                <th className="p-4 font-bold">Data / Hora</th>
                <th className="p-4 font-bold">Caminho Afetado (Destino)</th>
                <th className="p-4 font-bold">Status</th>
                <th className="p-4 font-bold text-right">Recuperação</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
              {filterHistory(historyLog, historyFilter).length === 0 ? (
                <tr><td colSpan="5" className="p-8 text-center text-gray-500">Nenhum registro encontrado.</td></tr>
              ) : (
                filterHistory(historyLog, historyFilter).map((log) => (
                  <tr key={log.id} className="hover:bg-gray-50 dark:hover:bg-gray-800/50">
                    <td className="p-4">
                      <div className="font-bold text-gray-900 dark:text-gray-100">{log.action}</div><div className="text-xs text-gray-500">{operationName(log)}</div>
                      <div className="text-xs text-gray-500">{log.details}</div>{log.reverted && <div className="mt-1 text-xs font-semibold text-gray-600 dark:text-gray-300">Criação já desfeita</div>}
                    </td>
                    <td className="p-4 text-gray-600 dark:text-gray-400">{new Date(log.date).toLocaleString('pt-BR')}</td>
                    <td className="p-4 font-mono text-xs break-all text-gray-800 dark:text-gray-200">{log.path}</td>
                    <td className="p-4">
                       <span className={`px-2 py-1 rounded text-xs font-bold uppercase ${log.status.includes('cancelado') ? 'bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-300' : log.status.includes('erro') ? 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400' : 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'}`}>
                         {log.status.split(':')[0]}
                       </span>
                    </td>
                    <td className="p-4 text-right">
                      <button onClick={() => showDialog('message', { type: log.status.includes('erro') ? 'error' : log.status.includes('cancelado') ? 'warning' : 'success', title: 'Detalhes do registro', message: [log.action, `Link: ${log.path}`, `Local dos dados: ${log.source || 'Não informado'}`, ...(log.outcome?.summary || []), log.metadata ? `Estratégia: ${log.metadata.strategy || 'criação'} · Backup: ${log.metadata.keepBackup ? 'mantido' : 'não se aplica'}` : '', `Resultado: ${log.status}`].filter(Boolean).join('\n') })} className="px-3 py-1.5 mr-2 mb-2 rounded border border-gray-300 dark:border-gray-600 hover:bg-gray-100 dark:hover:bg-gray-800 text-xs font-bold">Ver detalhes</button>
                      {canUndoRecord(log, links) && (
                        <button
                          onClick={() => openUndo(log.link)}
                          className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded shadow-sm hover:border-blue-500 hover:text-blue-600 dark:hover:text-blue-400 transition-colors text-xs font-bold"
                        >
                          <CornerUpLeft size={14} /> Desfazer
                        </button>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );

  const renderPropriedades = () => {
    const item = links.find(link => link.id === selectedItem?.id);
    if (!item) return <div className="p-6 space-y-4"><p>O link foi removido ou alterado. Consulte a lista atualizada.</p><button onClick={() => setCurrentScreen('principal')} className="px-4 py-2 rounded bg-blue-600 text-white">Voltar à lista</button></div>;
    return (
      <div className="screen-content flex-1 min-w-0 min-h-0 p-6 overflow-auto bg-gray-50 dark:bg-gray-900/30">
         <div className="mb-6 flex items-center gap-4">
            <button aria-label="Voltar à lista" onClick={() => setCurrentScreen('principal')} className="p-2 border rounded bg-white hover:bg-gray-100 dark:bg-gray-800 dark:border-gray-600"><CornerUpLeft size={20}/></button>
            <h2 className="text-2xl font-bold">Propriedades do Link</h2>
         </div>

         <div className="max-w-3xl bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl shadow-sm overflow-hidden">
            <div className="p-6 border-b border-gray-200 dark:border-gray-700 flex items-center gap-4">
               <div className="w-16 h-16 bg-blue-100 dark:bg-blue-900/30 text-blue-600 rounded-xl flex items-center justify-center">
                  {item.type.includes('Dir') || item.type === 'Junction' ? <Folder size={32} /> : <File size={32} />}
               </div>
               <div>
                  <h3 className="text-xl font-bold">{item.name}</h3>
                  <p className="text-gray-500 uppercase tracking-wider text-xs font-bold">{item.type} • Criado em {new Date(item.date.length === 10 ? `${item.date}T12:00:00-03:00` : item.date).toLocaleString('pt-BR')}</p>
               </div>
               <div className="ml-auto">
                 <span className={`px-3 py-1 rounded-full text-sm font-bold border ${item.status === 'Ativo' ? 'bg-green-50 border-green-200 text-green-700 dark:bg-green-900/20 dark:border-green-800 dark:text-green-400' : 'bg-red-50 border-red-200 text-red-700 dark:bg-red-900/20 dark:border-red-800 dark:text-red-400'}`}>
                   Status: {item.status}
                 </span>
               </div>
            </div>

            <div className="p-6 space-y-6 text-sm"><div className="flex flex-wrap gap-4"><p><strong>Criador:</strong> {item.creator}</p><label>Cenário de estatísticas<select value={statsMode} onChange={e=>setStatsMode(e.target.value)}><option value="ready">Concluídas</option><option value="loading">Calculando</option><option value="unavailable">Indisponíveis</option></select></label><label>Cenário de abertura<select value={folderScenario} onChange={e=>setFolderScenario(e.target.value)}><option value="available">Caminho disponível</option><option value="missing">Caminho inexistente</option></select></label></div>
               <div className="grid grid-cols-[150px_1fr] gap-4 items-center border-b border-gray-100 dark:border-gray-700 pb-4">
                  <div className="font-bold text-gray-500">Ponto de Acesso:</div>
                  <div className="font-mono bg-gray-50 dark:bg-gray-900 p-2 rounded border border-gray-200 dark:border-gray-700 break-all">{item.dest}</div>
               </div>
               <div className="grid grid-cols-[150px_1fr] gap-4 items-center border-b border-gray-100 dark:border-gray-700 pb-4">
                  <div className="font-bold text-gray-500">Alvo (Origem):</div>
                  <div className="font-mono bg-gray-50 dark:bg-gray-900 p-2 rounded border border-gray-200 dark:border-gray-700 break-all flex items-center justify-between">
                    {item.source}
                    {item.status === 'Quebrado' && <AlertTriangle size={16} className="text-red-500"/>}
                  </div>
               </div>
               <div className="grid grid-cols-[150px_1fr] gap-4 items-center">
                  <div className="font-bold text-gray-500">Estatísticas:</div>
                  <div className="text-gray-800 dark:text-gray-200">{statsMode === 'loading' ? <span role="status">Calculando tamanho, arquivos e pastas…</span> : item.status !== 'Ativo' || statsMode === 'unavailable' ? 'Indisponível: não foi possível consultar o caminho. Verifique acesso e conexão.' : <dl className="space-y-2"><div>Tamanho total: {formatSize(item.size)} (exemplo)</div><div>Arquivos: {item.files ?? 0}</div><div>Pastas: {item.folders ?? 0}</div>{item.type === 'Hardlink' && <p>Os nomes compartilham os mesmos dados; não some o tamanho por nome.</p>}<p className="text-xs text-gray-500">Valores fictícios, sem medição do computador.</p></dl>}</div>
               </div>
            </div>

            <div className="px-6 pb-6 flex flex-wrap gap-3"><button className="button-secondary" onClick={()=>describeOpen(item.source,item.status !== 'Ativo')}><FolderOpen size={16} className="mr-2"/>Abrir origem</button><button className="button-secondary" onClick={()=>describeOpen(item.dest)}><FolderOpen size={16} className="mr-2"/>Abrir destino</button><button className="button-secondary" onClick={()=>setStatsMode('loading')}>Recalcular estatísticas</button></div>
            <section className="p-6 border-t border-gray-200 dark:border-gray-700"><h3 className="font-bold mb-3">Histórico deste link</h3>{historyLog.some(row => row.linkId === item.id) ? historyLog.filter(row => row.linkId === item.id).map(row => <p key={row.id} className="text-sm mb-2">{new Date(row.date).toLocaleString('pt-BR')} · {row.action} · {row.status}</p>) : <p className="text-sm text-gray-500">Sem registros relacionados neste histórico.</p>}</section>
            <div className="p-4 bg-gray-50 dark:bg-gray-900 border-t border-gray-200 dark:border-gray-700 flex justify-end gap-3">
               <button onClick={() => openUndo(item)} className="px-4 py-2 flex items-center gap-2 bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-400 border border-red-200 dark:border-red-800 rounded hover:bg-red-100 transition-colors font-bold">
                  <Trash2 size={16}/> Reverter (Desfazer Link)
               </button>
            </div>
         </div>
      </div>
    );
  };

  const renderConfiguracoes = () => (
    <div className="screen-content flex-1 min-w-0 min-h-0 p-6 overflow-auto"><h2 className="text-2xl font-bold mb-4">Configurações do WinLink</h2><p className="mb-4">Preferências locais da demonstração. Salve para aplicar; restaurar padrões prepara os campos e também exige salvar.</p><div className="max-w-2xl space-y-5">
      <label className="block">Tema<select value={draft.theme} onChange={e => setDraft({ ...draft, theme: e.target.value })}><option value="auto">Seguir sistema</option><option value="dark">Escuro</option><option value="light">Claro</option></select></label>
      <label className="block">Tipo de link padrão<select value={draft.type} onChange={e => setDraft({ ...draft, type: e.target.value })}>{['Junction', 'Symlink (Dir)', 'Symlink (File)', 'Hardlink'].map(t => <option key={t}>{t}</option>)}</select></label>
      <label className="block">Diretórios de descoberta (um caminho absoluto por linha)<textarea rows={3} className="w-full" value={draft.directories} onChange={e => setDraft({ ...draft, directories: e.target.value })}/></label>
      <div className="space-y-3 rounded-xl border border-gray-200 dark:border-gray-700 p-4"><div className="flex justify-between items-center"><h3 className="font-bold">Diretórios configurados</h3><button className="button-secondary" onClick={()=>showDialog('directory')}>Adicionar diretório</button></div>{draft.directories.split(/\r?\n/).map(path=>path.trim()).filter(Boolean).map((path,index)=><div key={`${index}-${path}`} className="flex items-center justify-between gap-3"><span className="font-mono text-sm break-all">{path}</span><button className="button-secondary shrink-0" aria-label={`Remover diretório ${path}`} onClick={()=>setDraft(d=>({...d,directories:d.directories.split(/\r?\n/).map(p=>p.trim()).filter(p=>p && p!==path).join('\n')}))}>Remover</button></div>)}</div>
      <label className="flex items-start gap-3"><input type="checkbox" checked disabled readOnly/><span>Confirmar operações destrutivas <span className="text-gray-500">(obrigatório)</span><span className="block text-xs text-gray-500 mt-1">A prévia e a confirmação permanecem obrigatórias para proteger os dados.</span></span></label>
      {[['backup', 'Criar backup antes de desfazer'], ['notifications', 'Exibir notificações'], ['nested', 'Avisar sobre links aninhados']].map(([key, label]) => <label key={key} className="flex gap-3"><input type="checkbox" checked={draft[key]} onChange={e => setDraft({ ...draft, [key]: e.target.checked })}/>{label}</label>)}
      <label className="block">Nível de logs<select value={draft.logs} onChange={e => setDraft({ ...draft, logs: e.target.value })}>{['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'].map(t => <option key={t}>{t}</option>)}</select></label>
      <div className="flex flex-wrap items-end gap-3"><label className="text-sm">Cenário da pasta de logs<select value={folderScenario} onChange={e=>setFolderScenario(e.target.value)}><option value="available">Existe</option><option value="missing">Não existe</option></select></label><button className="button-secondary" onClick={()=>describeOpen('%APPDATA%/WinLink')}>Abrir pasta de logs</button></div>
      <p className="text-sm">Descoberta, notificações, avisos e logs: valores salvos para demonstrar as preferências; sem acesso ao sistema. Menu do Explorer, iniciar com Windows e monitoramento automático ficam fora deste escopo.</p>
      <div className="flex flex-wrap gap-4"><button className="button-secondary" onClick={() => setDraft({ ...DEFAULTS })}>Restaurar Padrões</button><button className="button-secondary" onClick={() => setDraft({ ...preferences })}>Descartar alterações</button><button onClick={savePreferences} className="bg-blue-600 text-white rounded px-4 py-2">Salvar Alterações</button></div>
    </div></div>
  );

  return (
    <div className={`flex flex-col h-screen min-h-0 overflow-hidden font-sans text-gray-900 dark:text-gray-100 bg-white dark:bg-gray-900`}>
      {renderDialogOverlay()}

      {/* Header */}
      <header inert={activeDialog ? '' : undefined} className="flex items-center justify-between p-4 bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700 z-10 shadow-sm shrink-0">
        <div className="flex items-center gap-3">
          <div className="p-1.5 bg-blue-600 rounded-md">
            <LinkIcon className="text-white" size={20} />
          </div>
          <h1 className="text-xl font-bold tracking-tight">WinLink <span className="font-normal text-sm text-gray-500">Manager</span></h1>
        </div>
        <div className="flex items-center gap-2">
          <button className="button-secondary" onClick={()=>showDialog('about')}>Sobre</button><button aria-label="Alternar Tema" onClick={() => { setPreferences(p=>({...p,theme:darkMode ? 'light' : 'dark'})); setDarkMode(!darkMode); setDraft(d => ({ ...d, theme: darkMode ? 'light' : 'dark' })); }} className="p-2 rounded-full hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-600 dark:text-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500" title="Alternar Tema">
            {darkMode ? <Sun size={20} /> : <Moon size={20} />}
          </button>
        </div>
      </header>

      {/* Main Layout */}
      <div className="flex flex-1 min-h-0 overflow-hidden" inert={activeDialog ? '' : undefined}>
        {/* Sidebar */}
        <div data-testid="sidebar" className="w-48 lg:w-64 bg-gray-50 dark:bg-gray-900 border-r border-gray-200 dark:border-gray-700 flex flex-col p-4 gap-2 shrink-0 overflow-y-auto">
          {[
            { id: 'principal', icon: <HardDrive size={18}/>, label: 'Meus Links' },
            { id: 'criar', icon: <Plus size={18}/>, label: 'Criar Novo' },
            { id: 'historico', icon: <Clock size={18}/>, label: 'Histórico' },
            { id: 'config', icon: <Settings size={18}/>, label: 'Configurações' },
          ].map(item => (
            <button
              key={item.id}
              disabled={Boolean(operationRef.current)}
              onClick={() => { if (!operationRef.current) setCurrentScreen(item.id); }}
              className={`flex items-center gap-3 p-3 rounded-lg text-left transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 font-bold ${currentScreen === item.id ? 'bg-blue-100 dark:bg-blue-900/40 text-blue-700 dark:text-blue-400' : 'text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-800'}`}
            >
              {item.icon} {item.label}
            </button>
          ))}
          <div className="mt-auto pt-4 border-t border-gray-200 dark:border-gray-700 text-xs text-gray-400 font-medium flex items-center gap-1">
            <Keyboard size={14}/> Navegável via Teclado (Tab/Enter)
          </div>
        </div>

        {/* Content Area */}
        {currentScreen === 'principal' && renderPrincipal()}
        {currentScreen === 'criar' && renderCriar()}
        {currentScreen === 'progresso' && renderProgresso()}
        {currentScreen === 'historico' && renderHistorico()}
        {currentScreen === 'propriedades' && renderPropriedades()}
        {currentScreen === 'config' && renderConfiguracoes()}
      </div>
    </div>
  );
}
