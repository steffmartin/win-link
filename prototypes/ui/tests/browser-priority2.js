async (page) => {
  const results = [];
  const check = (value, message) => { if (!value) throw new Error(message); };
  const reset = () => page.goto('http://127.0.0.1:5174/');
  const close = () => page.getByRole('button', { name: 'OK, Fechar', exact: true }).click();
  await reset();
  const dark = await page.getByTestId('sidebar').evaluate(el => getComputedStyle(el).backgroundColor);
  check(dark === 'rgb(17, 24, 39)', 'Menu lateral não está escuro');
  await page.getByRole('button', { name: 'Alternar Tema', exact: true }).click();
  check(await page.getByTestId('sidebar').evaluate(el => getComputedStyle(el).backgroundColor) === 'rgb(249, 250, 251)', 'Menu não acompanha tema claro');
  await page.getByRole('button', { name: 'Alternar Tema', exact: true }).click();
  check(await page.getByTestId('sidebar').evaluate(el => getComputedStyle(el).backgroundColor) === dark, 'Retorno ao escuro falhou');
  results.push('Tema do menu acompanha claro/escuro/escuro restaurado');
  for (const [strategy, keepBackup, expected] of [
    ['mover', false, 'Remover C:\\Projetos\\2022 somente depois'],
    ['mover', true, 'Manter C:\\Projetos\\2022 como backup'],
    ['duplicar', false, 'As duas pastas serão cópias independentes'],
    ['remover', false, 'pasta normal vazia'],
  ]) {
    await reset();
    await page.getByRole('button', { name: 'Histórico', exact: true }).click();
    await page.getByRole('button', { name: 'Desfazer', exact: true }).click();
    await page.locator(`input[name="undoStrat"][value="${strategy}"]`).check();
    if (strategy === 'mover') await page.getByLabel('Manter os dados na origem como backup após mover').setChecked(keepBackup);
    const preview = await page.locator('.fixed.inset-0').innerText();
    check(preview.includes('D:\\Archive\\2022') && preview.includes('C:\\Projetos\\2022'), 'Caminhos ausentes no diálogo');
    check(preview.includes(expected), 'Prévia não descreve o resultado esperado');
    await page.getByRole('button', { name: 'Executar Reversão', exact: true }).click();
    await page.getByRole('heading', { name: 'Reversão Concluída', exact: true }).waitFor();
    check((await page.locator('.fixed.inset-0').innerText()).includes(expected), 'Resultado não corresponde à prévia');
    await close();
    check(await page.getByText('Criação já desfeita', { exact: true }).count() === 1, 'Criação não marcada como desfeita');
    check(await page.getByRole('button', { name: 'Desfazer', exact: true }).count() === 0, 'Permite desfazer repetidamente');
    check(await page.locator('tbody tr').count() === 2, 'Registros não atualizados atomicamente');
    await page.getByRole('button', { name: 'Ver detalhes', exact: true }).first().click();
    check((await page.locator('.fixed.inset-0').innerText()).includes(`Backup: ${keepBackup ? 'mantido' : 'não se aplica'}`), 'Metadata de backup incorreta');
    await close();
    await page.getByRole('button', { name: 'Meus Links', exact: true }).click();
    check(await page.getByRole('heading', { name: 'Projetos_Antigos', exact: true }).count() === 0, 'Link permaneceu na lista');
    check(await page.getByRole('heading', { name: 'Config_Global', exact: true }).count() === 1, 'Outro link foi removido');
    if (strategy === 'duplicar') {
      await page.getByRole('button', { name: 'Criar Novo', exact: true }).click();
      await page.locator('#creation-source').fill('E:\\NovaOrigem');
      await page.locator('#creation-dest').fill('D:\\Archive\\2022');
      check(await page.getByRole('combobox', { name: 'Estado do caminho do link' }).inputValue() === 'directory', 'Pasta restaurada tratada como caminho inexistente');
      await page.getByRole('button', { name: 'Avançar', exact: true }).click();
      check((await page.locator('.fixed.inset-0').innerText()).includes('Copiar os arquivos'), 'Criação posterior não reconhece migração necessária');
    }
    results.push(`Reversão de diretório ${strategy}, backup ${keepBackup}: prévia, resultado, lista e histórico coerentes`);
  }
  await reset();
  await page.getByTestId('link-card-1').getByRole('button').click();
  check(await page.getByRole('heading', { name: 'Histórico deste link', exact: true }).count() === 1, 'Propriedades não mostram histórico relacionado');
  await page.getByRole('button', { name: 'Reverter (Desfazer Link)', exact: true }).click();
  await page.getByRole('button', { name: 'Cancelar', exact: true }).click();
  check(await page.getByRole('heading', { name: 'Propriedades do Link', exact: true }).isVisible(), 'Cancelar perdeu as propriedades');
  await page.getByRole('button', { name: 'Reverter (Desfazer Link)', exact: true }).click();
  await page.locator('input[name="undoStrat"][value="remover"]').check();
  await page.getByRole('button', { name: 'Executar Reversão', exact: true }).click();
  await close();
  check(await page.getByRole('heading', { name: 'Meus Links', exact: true }).isVisible(), 'Propriedades não retornaram à lista atualizada');
  results.push('Reversão pelas propriedades: cancelar preserva seleção; confirmar retorna à lista atualizada');
  await reset();
  await page.getByTestId('link-card-3').getByRole('button').click();
  await page.getByRole('button', { name: 'Reverter (Desfazer Link)', exact: true }).click();
  check(await page.getByRole('radio').count() === 0, 'Hard link oferece estratégias de diretório');
  check(!(await page.locator('.fixed.inset-0').innerText()).includes('pasta normal vazia'), 'Hard link promete pasta vazia');
  await page.getByRole('button', { name: 'Executar Reversão', exact: true }).click();
  await close();
  check(await page.getByRole('heading', { name: 'hosts_backup', exact: true }).count() === 0, 'Nome de hard link não foi removido');
  results.push('Hard link: remove somente o nome e não oferece estratégias de pasta');
  await reset();
  await page.getByRole('button', { name: 'Criar Novo', exact: true }).click();
  await page.getByRole('button', { name: /^Symlink \(File\)/ }).click();
  await page.locator('#creation-source').fill('C:\\Dados\\original.txt');
  await page.locator('#creation-dest').fill('D:\\Links\\referencia.txt');
  await page.getByRole('button', { name: 'Avançar', exact: true }).click();
  await page.getByRole('button', { name: 'Confirmar e Iniciar', exact: true }).click();
  await page.getByRole('heading', { name: 'Criação Bem-sucedida', exact: true }).waitFor({ timeout: 6000 });
  await page.getByRole('button', { name: 'Ir para Lista', exact: true }).click();
  check(await page.getByRole('heading', { name: 'referencia.txt', exact: true }).count() === 1, 'Arquivo criado ausente');
  await page.getByRole('button', { name: 'Histórico', exact: true }).click();
  await page.getByRole('button', { name: 'Desfazer', exact: true }).first().click();
  check(await page.getByRole('radio').count() === 0, 'Symlink de arquivo oferece mover/duplicar');
  check((await page.locator('.fixed.inset-0').innerText()).includes('C:\\Dados\\original.txt'), 'Registro criado perdeu o caminho de origem');
  await page.getByRole('button', { name: 'Executar Reversão', exact: true }).click();
  await close();
  check(await page.getByRole('button', { name: 'Desfazer', exact: true }).count() === 1, 'Desfazer alterou a criação de outro link');
  await page.getByRole('button', { name: 'Meus Links', exact: true }).click();
  check(await page.getByRole('heading', { name: 'referencia.txt', exact: true }).count() === 0, 'Reversão do arquivo não atualizou a lista');
  check(await page.getByRole('heading', { name: 'Projetos_Antigos', exact: true }).count() === 1, 'Registro desfez link incorreto');
  results.push('Criar e desfazer arquivo pelo histórico mantém identidade e preserva outros links');
  await reset();
  return { passed: true, results };
}
