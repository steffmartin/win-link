import test from 'node:test';
import assert from 'node:assert/strict';
import { applyUndo, canUndoRecord, historyRecord, undoError } from '../src/history.js';
import { normalizePath } from '../src/model.js';
const link = { id: 'link-1', source: 'D:\\Dados\\Projetos', dest: 'C:\\Links\\Projetos', type: 'Junction', status: 'Ativo' };
const other = { id: 'link-2', source: 'D:\\Outros', dest: 'C:\\Links\\Outros', type: 'Junction', status: 'Ativo' };
function stateFor(item = link) { return { links: [{ ...item }, { ...other }], history: [historyRecord({ id: 'create-1', action: 'Criação', link: item })], paths: {} }; }
const options = (expected = link, strategy = 'mover', keepBackup = false) => ({ expected, strategy, keepBackup, recordId: 'undo-1', date: '2026-11-03T12:00:00Z' });
for (const [strategy, backup, targetState, sourceState] of [
  ['mover', false, 'restored-directory', 'removed-after-restore'],
  ['mover', true, 'restored-directory', 'preserved-directory'],
  ['duplicar', false, 'restored-directory', 'preserved-directory'],
  ['remover', false, 'empty-directory', 'preserved-directory'],
]) {
  test(`diretório: ${strategy}, backup ${backup}`, () => {
    const previous = stateFor(); const frozen = JSON.stringify(previous);
    const result = applyUndo(previous, options(link, strategy, backup));
    assert.deepEqual(result.state.links, [other]);
    assert.equal(result.outcome.targetState, targetState);
    assert.equal(result.outcome.sourceState, sourceState);
    assert.equal(result.outcome.keepBackup, strategy === 'mover' && backup);
    assert.equal(result.record.linkId, link.id);
    assert.equal(result.record.source, link.source);
    assert.equal(result.state.history[1].reverted, true);
    assert.equal(result.state.history[1].reversedBy, result.record.id);
    assert.equal(canUndoRecord(result.state.history[1], result.state.links), false);
    assert.equal(JSON.stringify(previous), frozen, 'A transição não pode mutar o estado anterior');
  });
}
for (const type of ['Hardlink', 'Symlink (File)']) {
  test(`arquivo ${type}: remover nome sem criar pasta`, () => {
    const item = { ...link, type, source: 'C:\\Dados\\original.txt', dest: 'C:\\Links\\referencia.txt' };
    const result = applyUndo(stateFor(item), options(item, 'remover', true));
    assert.equal(result.outcome.targetState, 'removed-name');
    assert.equal(result.outcome.sourceState, 'unchanged-file');
    assert.equal(result.outcome.keepBackup, false);
    assert.equal(result.state.paths[normalizePath(item.dest)].kind, 'missing');
    assert.equal(result.state.paths[normalizePath(item.source)].kind, 'file');
    assert.ok(!result.outcome.summary.join(' ').includes('pasta normal vazia'));
  });
  test(`arquivo ${type}: recusa estratégia de diretório`, () => assert.throws(() => applyUndo(stateFor({ ...link, type }), options({ ...link, type }, 'duplicar')), /apenas o nome/));
}
test('histórico identifica exatamente o link da criação', () => {
  const original = stateFor();
  assert.equal(original.history[0].linkId, link.id);
  assert.deepEqual(original.history[0].link, link);
  assert.ok(canUndoRecord(original.history[0], original.links));
});
test('reversão repetida é recusada', () => {
  const first = applyUndo(stateFor(), options());
  assert.throws(() => applyUndo(first.state, options()), /não está mais disponível/);
});
test('não desfaz um substituto no mesmo caminho', () => {
  const original = stateFor();
  const replacement = { ...link, id: 'link-recreated' };
  assert.equal(canUndoRecord(original.history[0], [replacement]), false);
  assert.throws(() => applyUndo({ ...original, links: [replacement] }, options()), /não está mais disponível/);
});
for (const field of ['source', 'dest', 'type']) {
  test(`recusa seleção antiga após mudar ${field}`, () => {
    const changed = { ...link, [field]: field === 'type' ? 'Symlink (Dir)' : 'E:\\Alterado' };
    assert.throws(() => applyUndo({ ...stateFor(), links: [changed] }, options()), /foi alterado/);
  });
}
test('não oferece desfazer para erro, cancelamento ou operação de reversão', () => {
  for (const status of ['erro: sem acesso', 'cancelado']) assert.equal(canUndoRecord(historyRecord({ action: 'Criação', link, status }), [link]), false);
  assert.equal(canUndoRecord(historyRecord({ action: 'Reversão', link }), [link]), false);
});
test('registro sem identidade não pode desfazer por aproximação de caminho', () => assert.equal(canUndoRecord({ action: 'Criação', status: 'sucesso', path: link.dest }, [link]), false));
test('origem indisponível permite remover só o link', () => {
  const broken = { ...link, status: 'Quebrado' };
  assert.ok(undoError([broken], broken, 'mover'));
  assert.equal(undoError([broken], broken, 'remover'), null);
  assert.equal(applyUndo(stateFor(broken), options(broken, 'remover')).outcome.targetState, 'empty-directory');
});
test('arquivo indisponível bloqueia reversão sem inventar estado de dados', () => {
  const broken = { ...link, type: 'Hardlink', status: 'Quebrado' };
  const before = stateFor(broken);
  assert.throws(() => applyUndo(before, options(broken, 'remover')), /identidade/);
  assert.equal(before.links.length, 2);
  assert.equal(before.paths[normalizePath(broken.source)], undefined);
});

test('a existência da pasta restaurada é preservada para a criação seguinte', () => {
  const result = applyUndo(stateFor(), options(link, 'duplicar'));
  assert.equal(result.state.paths[normalizePath(link.dest)].kind, 'directory');
  assert.equal(result.state.paths[normalizePath(link.dest)].content, 'restored-data');
  assert.equal(result.state.paths[normalizePath(link.source)].kind, 'directory');
});

test('recusa registro cujo identificador diverge do snapshot', () => {
  const record = historyRecord({ action: 'Criação', link });
  assert.equal(canUndoRecord({ ...record, linkId: 'other-id' }, [link]), false);
});
