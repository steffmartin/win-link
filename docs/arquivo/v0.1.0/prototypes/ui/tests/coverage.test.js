import test from 'node:test';
import assert from 'node:assert/strict';
import { operationName, sortedLinks, dateRange, formatSize } from '../src/coverage.js';
import { filterHistory, validatePreferences, DEFAULTS } from '../src/controls.js';
test('operação e tipo de link são filtros independentes',()=>{
 const rows=[{action:'Criação',type:'Junction',status:'sucesso',date:'2026-11-03T12:00:00'},{action:'Reversão',type:'Junction',status:'sucesso',date:'2026-11-03T12:00:00'}];
 assert.equal(filterHistory(rows,{operation:'Desfazer',type:'Junction'}).length,1);
 assert.equal(operationName({action:'Criação',type:'Hardlink'}),'Criar Hardlink');
});
test('ordenação numérica usa tamanho e preserva a lista original',()=>{
 const rows=[{size:20},{size:null},{size:100}];assert.deepEqual(sortedLinks(rows,'size','desc').map(x=>x.size),[100,20,null]);assert.equal(rows[0].size,20);
});
test('períodos usam datas locais e personalizado mantém datas',()=>{
 const now=new Date(2026,10,3,12);assert.deepEqual(dateRange('week',now),{from:'2026-10-27',to:'2026-11-03'});assert.deepEqual(dateRange('custom',now),{});assert.deepEqual(dateRange('all',now),{from:'',to:''});
});
test('diretórios não podem ficar vazios e tamanho indisponível não vira zero',()=>{
 assert.equal(validatePreferences({...DEFAULTS,directories:'  '}).length,1);assert.equal(formatSize(null),'Indisponível');assert.equal(formatSize(0),'0.0 KiB');
});
