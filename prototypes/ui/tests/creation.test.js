import test from 'node:test';
import assert from 'node:assert/strict';
import { normalizePath, validateCreation } from '../src/model.js';
const local = { source: 'D:\\Dados\\Projetos', dest: 'C:\\Links\\Projetos', type: 'Junction' };
const file = { source: 'C:\\Dados\\relatorio.txt', dest: 'C:\\Links\\relatorio.txt', type: 'Hardlink', sourceKind: 'file' };
const reject = (input, message) => assert.ok(validateCreation(input).some(error => message.test(error)), JSON.stringify(validateCreation(input)));
for (const type of ['Junction', 'Symlink (Dir)', 'Symlink (File)', 'Hardlink']) {
  test(`cria ${type} com cenário válido`, () => assert.deepEqual(validateCreation(type.includes('File') || type === 'Hardlink' ? { ...file, type } : { ...local, type }), []));
}
for (const variant of ['D:\\Dados\\Projetos', 'd:/dados/projetos/', ' D:\\Dados\\.\\Projetos\\ ', 'D:\\Dados\\Outro\\..\\Projetos']) {
  test(`rejeita alias igual: ${variant}`, () => reject({ ...local, dest: variant }, /caminhos diferentes/));
}
test('normalização preserva compartilhamento e reduz componentes', () => assert.equal(normalizePath('\\\\Servidor\\Share\\Dados\\..\\Projetos'), '\\\\servidor\\share\\projetos'));
for (const bad of ['', '   ', 'pasta\\projetos', 'C:Projetos', 'C:\\', 'C:\\Dados\\..', '\\\\server\\share\\', 'C:\\Dados\\a?.txt', 'C:\\Dados\\NUL.txt', 'C:\\Dados\\final.', 'C:\\Dados\\com espaço \\arquivo', '\\\\?\\C:\\Dados', 'C:\\Dados\\file:stream']) {
  test(`rejeita caminho inválido: ${JSON.stringify(bad)}`, () => assert.ok(validateCreation({ ...local, source: bad }).length));
}
for (const dest of ['D:\\Dados', 'D:\\Dados\\Projetos\\Filho']) {
  test(`rejeita sobreposição: ${dest}`, () => reject({ ...local, dest }, /caminhos diferentes/));
}
test('não confunde nomes com mesmo prefixo', () => assert.deepEqual(validateCreation({ ...local, dest: 'D:\\Dados\\Projetos2' }), []));
test('aceita espaços e Unicode válidos', () => assert.deepEqual(validateCreation({ ...local, source: 'D:\\Ação e projetos\\Relatórios' }), []));
test('permite pasta de origem ausente em criação simples', () => assert.deepEqual(validateCreation({ ...local, sourceExists: false, sourceKind: 'missing' }), []));
test('permite migrar pasta anterior para nova origem', () => assert.deepEqual(validateCreation({ ...local, sourceExists: false, sourceKind: 'missing', targetExists: true, targetKind: 'directory' }), []));
test('bloqueia colisões antes de migrar', () => reject({ ...local, targetExists: true, targetKind: 'directory', copyConflicts: true }, /conflitos/));
test('bloqueia arquivo no lugar de pasta de origem', () => reject({ ...local, sourceKind: 'file' }, /deve ser uma pasta/));
test('bloqueia arquivo no lugar da pasta a migrar', () => reject({ ...local, targetExists: true, targetKind: 'file' }, /contém um arquivo/));
for (const type of ['Symlink (File)', 'Hardlink']) {
  test(`${type}: exige arquivo existente`, () => reject({ ...file, type, sourceExists: false }, /arquivo existente/));
  test(`${type}: recusa pasta como origem`, () => reject({ ...file, type, sourceKind: 'directory' }, /arquivo existente/));
  test(`${type}: não substitui caminho existente`, () => reject({ ...file, type, targetExists: true }, /já existe/));
}
test('hard link recusa outro volume', () => reject({ ...file, dest: 'D:\\Links\\relatorio.txt' }, /mesmo volume/));
test('hard link admite nome de arquivo sem extensão', () => assert.deepEqual(validateCreation({ ...file, source: 'C:\\Dados\\LICENSE', dest: 'C:\\Links\\LICENSE' }), []));
test('symlink de arquivo admite outro volume', () => assert.deepEqual(validateCreation({ ...file, type: 'Symlink (File)', dest: 'D:\\Links\\relatorio.txt' }), []));
test('junction recusa pasta de rede', () => reject({ ...local, source: '\\\\server\\share\\Dados' }, /discos locais/));
test('symlink de diretório admite pasta de rede', () => assert.deepEqual(validateCreation({ ...local, type: 'Symlink (Dir)', source: '\\\\server\\share\\Dados' }), []));
test('não substitui link da lista, ignorando caixa e separadores', () => reject({ ...local, existingLinks: [{ source: 'D:\\Real', dest: 'c:/links/projetos/', type: 'Junction' }] }, /já é um link/));
test('não substitui link fictício mesmo se ainda não consta na lista', () => reject({ ...local, targetKind: 'link', targetExists: true }, /já é um link/));
test('detecta sobreposição por alias de link conhecido', () => reject({ ...local, source: 'C:\\Alias\\Filho', dest: 'D:\\Real', existingLinks: [{ source: 'D:\\Real', dest: 'C:\\Alias', type: 'Junction' }] }, /resolvem/));
test('detecta ciclo existente na resolução de aliases', () => reject({ ...local, source: 'C:\\AliasA\\Filho', existingLinks: [{ source: 'C:\\AliasB', dest: 'C:\\AliasA', type: 'Junction' }, { source: 'C:\\AliasA', dest: 'C:\\AliasB', type: 'Junction' }] }, /cíclicos/));
test('impede criar caminho dentro de árvore redirecionada', () => reject({ ...local, dest: 'C:\\Alias\\Novo', existingLinks: [{ source: 'E:\\Real', dest: 'C:\\Alias', type: 'Junction' }] }, /passa por um link existente/));
