async page => {
 const results=[],check=(v,m)=>{if(!v)throw Error(m)};
 const reset=async()=>{await page.goto('http://127.0.0.1:5174/');await page.getByRole('button',{name:'Histórico',exact:true}).click();await page.getByRole('button',{name:'Desfazer',exact:true}).click();};
 for(const scenario of ['copy','changed','cleanup','space','restored','cancel','none']) {
  await reset();if(!['cancel','none'].includes(scenario))await page.getByRole('combobox',{name:'Cenário da reversão'}).selectOption(scenario);
  await page.getByRole('button',{name:'Executar Reversão'}).click();await page.getByRole('heading',{name:'Reversão em Andamento'}).waitFor();
  if(scenario==='cancel'){await page.getByRole('button',{name:'Interromper',exact:true}).click();await page.getByText('Cancelando / preservando dados…').waitFor();await page.getByRole('heading',{name:'Cancelado',exact:true}).waitFor();await page.getByRole('button',{name:'Voltar à seleção'}).click();}
  else if(scenario==='none'){await page.getByRole('dialog',{name:'Reversão Concluída'}).waitFor();await page.getByRole('button',{name:'OK, Fechar'}).click();}
  else {await page.getByRole('heading',{name:'Falha na Operação'}).waitFor();check((await page.locator('body').innerText()).includes(scenario==='restored'?'Não repita a reversão':'preservad')||scenario==='space','Preservação');await page.getByRole('button',{name:'Voltar à seleção'}).click();}
  await page.getByRole('button',{name:'Meus Links',exact:true}).click();check(await page.getByRole('heading',{name:'Projetos_Antigos',exact:true}).count()===(['none','restored'].includes(scenario)?0:1),'Estado incorreto '+scenario);results.push(scenario);
 }
 await page.reload();return {passed:true,results};
}