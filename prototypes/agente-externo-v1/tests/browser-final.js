async page => {
 const results=[], errors=[]; page.on('pageerror',e=>errors.push(e.message));
 const check=(v,m)=>{if(!v)throw Error(m)};
 const reset=async()=>{await page.goto('http://127.0.0.1:5174/');};
 await reset();
 for(const scenario of ['occupied','permission','space','unavailable','backup','history']) {
  await reset();await page.getByRole('button',{name:'Criar Novo',exact:true}).click();
  await page.locator('#creation-source').fill('D:\\Dados\\Teste');await page.locator('#creation-dest').fill('C:\\Links\\Teste');
  if(scenario==='backup')await page.getByRole('combobox',{name:'Estado do caminho do link'}).selectOption('directory');
  await page.getByRole('combobox',{name:'Cenário de operação'}).selectOption(scenario);
  await page.getByRole('button',{name:'Avançar',exact:true}).click();
  const dialog=page.getByRole('dialog');
  await page.keyboard.press('Shift+Tab');check(await dialog.getByRole('button',{name:'Confirmar e Iniciar'}).evaluate(el=>el===document.activeElement),'Foco não contido');
  await page.getByRole('button',{name:'Confirmar e Iniciar'}).click();
  if(['backup','history'].includes(scenario)) {
   await page.getByRole('heading',{name:'Criação Bem-sucedida'}).waitFor();
   check((await page.locator('body').innerText()).includes(scenario==='backup'?'.winlink-backup':'registro do histórico falhou'),'Aviso ausente');
   await page.getByRole('button',{name:'Ir para Lista'}).click();check(await page.getByRole('heading',{name:'Teste',exact:true}).count()===1,'Link ausente');
   if(scenario==='history'){await page.getByRole('button',{name:'Histórico',exact:true}).click();check(await page.locator('tbody tr').count()===1,'Histórico fictício foi gravado apesar da falha');}
  } else { await page.getByRole('heading',{name:'Falha na Operação'}).waitFor();await page.getByRole('button',{name:'Voltar para Edição'}).click();check(await page.locator('#creation-source').inputValue()==='D:\\Dados\\Teste','Edição não preservada'); }
  results.push(scenario);
 }
 await reset();await page.getByRole('combobox',{name:'Cenário da atualização'}).selectOption('failure');await page.getByRole('button',{name:/^Atualizar/}).click();await page.getByRole('alert').waitFor();check(await page.getByRole('heading',{level:4}).count()===6,'Cache perdido');await page.getByRole('combobox',{name:'Cenário da atualização'}).selectOption('success');await page.getByRole('button',{name:'Tentar novamente'}).click();await page.getByRole('alert').waitFor({state:'detached'});results.push('cache preservado e recuperado');
 for(const width of [760,1024]) {
  await page.setViewportSize({width,height:700});
  for(const screen of ['Meus Links','Criar Novo','Histórico','Configurações']) {
   await page.getByRole('button',{name:screen,exact:true}).click();check(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'Overflow da página '+screen);
  }
  await page.getByRole('button',{name:'Alternar Tema',exact:true}).click();
 }
 check(!errors.length,errors.join('\n'));await page.setViewportSize({width:1280,height:900});await reset();return {passed:true,results,errors};
}