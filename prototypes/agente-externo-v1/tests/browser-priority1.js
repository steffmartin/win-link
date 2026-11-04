async (page) => {
  const results = [];
  const check = (condition, text) => { if (!condition) throw new Error(text); };
  const createScreen = async () => { await page.goto('http://127.0.0.1:5174/'); await page.getByRole('button', { name: 'Criar Novo', exact: true }).click(); };
  const fill = async (source, dest) => { await page.locator('#creation-source').fill(source); await page.locator('#creation-dest').fill(dest); };
  const invalid = async text => {
    await page.getByRole('button', { name: 'Avançar', exact: true }).click();
    await page.getByRole('heading', { name: 'Revise os caminhos', exact: true }).waitFor();
    check((await page.locator('body').innerText()).includes(text), `Mensagem ausente: ${text}`);
    check(await page.getByRole('heading', { name: 'Confirmar Criação de Link' }).count() === 0, 'Caminho inválido chegou à confirmação');
    await page.getByRole('button', { name: 'OK, Fechar', exact: true }).click();
  };
  await createScreen();
  await fill('C:\\Dados\\.\\Projetos', 'c:/dados/projetos/');
  check(await page.locator('#creation-dest').evaluate(el => el === document.activeElement), 'Campo perdeu foco');
  await invalid('caminhos diferentes'); results.push('Igualdade normalizada bloqueada; foco preservado');
  await fill('projeto-relativo', 'D:\\Links\\Projeto'); await invalid('caminho absoluto');
  await fill('C:\\Dados', 'C:\\Dados\\Filho'); await invalid('caminhos diferentes');
  await fill('C:\\Dados', 'd:/archive/2022/'); await invalid('já é um link');
  results.push('Relativos, sobreposição e link existente bloqueados');
  await page.getByRole('button', { name: /^Hardlink/ }).click();
  await fill('C:\\Dados\\arquivo.txt', 'D:\\Links\\arquivo.txt'); await invalid('mesmo volume');
  await fill('C:\\Dados\\arquivo.txt', 'C:\\Links\\arquivo.txt');
  await page.getByRole('combobox', { name: 'Estado do local dos dados' }).selectOption('missing'); await invalid('arquivo existente');
  await page.getByRole('combobox', { name: 'Estado do local dos dados' }).selectOption('file');
  await page.getByRole('combobox', { name: 'Estado do caminho do link' }).selectOption('file'); await invalid('já existe');
  results.push('Hard link: volume, existência e nome livre exigidos');
  await createScreen(); await fill('D:\\Dados\\Migracao', 'C:\\Links\\Migracao');
  await page.getByRole('combobox', { name: 'Estado do caminho do link' }).selectOption('directory');
  await page.getByLabel('Há arquivos com o mesmo nome nas duas pastas').check(); await invalid('conflitos');
  await page.getByLabel('Há arquivos com o mesmo nome nas duas pastas').uncheck();
  await page.getByRole('button', { name: 'Avançar', exact: true }).click();
  check((await page.locator('body').innerText()).includes('backup temporário'), 'Prévia não explica preservação da pasta');
  await page.getByRole('button', { name: 'Confirmar e Iniciar', exact: true }).click();
  check(await page.getByRole('button', { name: 'Criar Novo', exact: true }).isDisabled(), 'Outra criação pode entrar durante a operação');
  await page.getByRole('button', { name: 'Interromper', exact: true }).click();
  await page.waitForTimeout(3300);
  check(await page.getByRole('heading', { name: 'Cancelado', exact: true }).isVisible(), 'Cancelamento não permaneceu cancelado');
  results.push('Migração: conflito bloqueado, preservação explicada, reentrada impedida e cancelamento mantido');
  for (const [type, file, source, dest] of [
    ['Junction', false, 'D:\\Dados\\PastaNova', 'C:\\Links\\PastaNova'],
    ['Symlink (Dir)', false, 'D:\\Dados\\Simbolico', 'C:\\Links\\Simbolico'],
    ['Symlink (File)', true, 'C:\\Dados\\fonte.txt', 'D:\\Links\\simbolico.txt'],
    ['Hardlink', true, 'C:\\Dados\\fonte.txt', 'C:\\Links\\outro-nome.txt'],
  ]) {
    await createScreen();
    await page.getByRole('button', { name: new RegExp('^' + type.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')) }).click();
    await fill(source, dest);
    if (file) {
      await page.getByRole('button', { name: 'Procurar', exact: true }).first().click();
      check((await page.locator('body').innerText()).includes('C:\\Dados\\arquivo.txt'), 'Seletor de arquivo não oferece arquivos');
      await page.getByRole('button', { name: 'Fechar', exact: true }).count().then(async count => {
        if (count) await page.getByRole('button', { name: 'Fechar', exact: true }).click();
        else await page.locator('.fixed.inset-0 button').first().click();
      });
    } else {
      await page.getByRole('combobox', { name: 'Estado do local dos dados' }).selectOption('missing');
    }
    await page.getByRole('button', { name: 'Avançar', exact: true }).click();
    await page.getByRole('heading', { name: 'Confirmar Criação de Link' }).waitFor();
    if (type === 'Hardlink') check((await page.locator('body').innerText()).includes('não há uma cópia independente'), 'Prévia de hard link incorreta');
    await page.getByRole('button', { name: 'Confirmar e Iniciar', exact: true }).click();
    await page.getByRole('heading', { name: 'Criação Bem-sucedida', exact: true }).waitFor({ timeout: 6000 });
    await page.getByRole('button', { name: 'Ir para Lista', exact: true }).click();
    const newName = dest.split('\\').at(-1);
    check(await page.getByRole('heading', { name: newName, exact: true }).count() === 1, `${type} adicionou link duplicado ou nenhum`);
    results.push(`Criação válida de ${type}: exatamente um link`);
  }
  await page.goto('http://127.0.0.1:5174/');
  return { passed: true, results };
}
