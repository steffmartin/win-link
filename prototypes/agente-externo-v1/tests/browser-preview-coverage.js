async page => {
 const check=(v,m)=>{if(!v)throw Error(m)},results=[];
 await page.goto('http://127.0.0.1:5174/');await page.getByRole('button',{name:'Criar Novo',exact:true}).click();await page.locator('#creation-source').fill('D:/Dados/Previa');await page.locator('#creation-dest').fill('C:/Links/Previa');await page.getByRole('combobox',{name:'Estado do caminho do link'}).selectOption('directory');
 for(const scenario of ['space','nested','processes','calculating']) {
  await page.getByRole('combobox',{name:'Cenário da prévia'}).selectOption(scenario);await page.getByRole('button',{name:'Avançar',exact:true}).click();const confirm=page.getByRole('button',{name:'Confirmar e Iniciar'});
  if(scenario==='space')check(await confirm.isDisabled(),'Espaço não bloqueou');
  if(scenario==='nested')check(await page.getByText('Links aninhados encontrados',{exact:true}).count()===1,'Aninhados');
  if(scenario==='processes'){check(await confirm.isDisabled(),'Processos não bloqueou');await page.getByRole('button',{name:'Simular processos liberados'}).click();check(await confirm.isEnabled(),'Liberar processos');}
  if(scenario==='calculating'){check(await confirm.isDisabled(),'Calculando não bloqueou');await page.getByRole('button',{name:'Concluir cálculo simulado'}).click();check(await confirm.isEnabled(),'Cálculo não liberou');}
  await page.getByRole('button',{name:'Revisar',exact:true}).click();results.push(scenario);
 }
 await page.reload();return {passed:true,results};
}