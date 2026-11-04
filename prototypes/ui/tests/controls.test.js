import test from 'node:test';
import assert from 'node:assert/strict';
import { DEFAULTS, validatePreferences, loadPreferences, filterHistory } from '../src/controls.js';
test('rejeita descoberta relativa e aceita caminhos absolutos', () => {
 assert.equal(validatePreferences({ ...DEFAULTS, directories: 'relativo' }).length, 1);
 assert.deepEqual(validatePreferences(DEFAULTS), []);
});
test('storage indisponível ou inválido retorna padrões', () => {
 globalThis.localStorage = { getItem: () => '{bad' }; assert.deepEqual(loadPreferences(), DEFAULTS);
 globalThis.localStorage = { getItem: () => JSON.stringify({ ...DEFAULTS, backup: 'false' }) }; assert.deepEqual(loadPreferences(), DEFAULTS);
});
test('filtros combinam tipo resultado e limites inclusivos locais', () => {
 const rows = [{ type:'Junction',status:'sucesso',date:'2026-11-03T12:00:00' },{ type:'Hardlink',status:'erro: acesso',date:'2026-11-02T12:00:00' }];
 assert.equal(filterHistory(rows, {type:'Junction',result:'sucesso',from:'2026-11-03',to:'2026-11-03'}).length,1);
 assert.equal(filterHistory(rows, {result:'erro'}).length,1);
 assert.equal(filterHistory(rows, {from:'2026-11-04',to:'2026-11-01'}).length,0);
});
