# Estado atual

Data de entrega: 20 de novembro de 2026. Versão: 0.1.0.
Repositório público: https://github.com/andrew-drew-beep/treasury-bridge-core

## Entrega funcional
Domínio com Decimal; três layouts CSV; XLSX opcional; motor 1:1 por CNPJ/valor/escopo/data/referência;
conferência separada de IN/OUT; relatórios por conta; exceções dos dois lados; revisão humana entre candidatos;
SQLite persistente; histórico; exportação CSV/JSON; interface web local e CLI; massa sintética de 12 contas.
Mapeamento, contratos, decisões e roteiro de continuidade estão em docs/ e AGENTS.md.
Currículo atualizado separadamente com a PoC e seu link. Nenhum currículo está publicado aqui.

## Evidências de verificação
- 33 testes automatizados passaram localmente em Python 3.12, com XLSX.
- Os mesmos 33 testes e a execução CLI passaram no GitHub em Python 3.11, 3.12 e 3.13.
- O teste Chromium scripts/smoke_browser.py passou no GitHub: abrir cenário, filtrar cinco pendências,
  aprovar B001/L001, recarregar histórico, baixar CSV e reimportar os três layouts pela interface.
- Sem erros JavaScript; largura mobile verificada em 390 px. Capturas desktop e mobile foram inspecionadas.
- Run de CI completo com quatro jobs verdes:
  https://github.com/andrew-drew-beep/treasury-bridge-core/actions/runs/44822211237
- Código funcional validado no commit 1f481d8ccf4bbb94bc5b65827dd894bc2fc16e08.
  Commits seguintes de documentação não alteram esse comportamento.
- CLI: 20 movimentos bancários, 19 contábeis; 15 sugestões por regra, 2 ambiguidades,
  1 CNPJ ausente e 2 sem correspondência. DEMO-02/OUT tem diferença de 20,00 BRL.
- Capturas do CI disponíveis no artefato browser-check, sujeito à retenção do GitHub.

## Limite do ambiente de construção
O navegador conectado não acessa o loopback do executor e o Chromium local não iniciou nesse ambiente.
A verificação de interface foi concluída usando o runner do GitHub; não ficou bloqueada por essa limitação.

## Fora da versão
Integração SAP/bancos/PowerApps, dados reais, pagamentos parciais/agrupados, conversão cambial, IA/LLM,
previsões de câmbio, contas reais e autenticação corporativa. Não alegar implantação ou ganhos operacionais reais.

## Retomada
Leia AGENTS.md e docs/HANDOFF.md. Execute:
`python -m unittest discover -s tests -v`
`python run.py demo`
`python run.py serve`
Abra http://127.0.0.1:8765.
O pacote base não exige dependências; XLSX requer o extra excel.
Próxima evolução proposta: mapping configurável e seleção explícita de período.

## Atualização de navegação
Implementado atalho Há pendências → na tabela de fechamento. Aplica recorte completo por empresa,
conta bancária, conta contábil, moeda e direção; filtra as duas listas e navega para a pendência.
Inclui botão Ver todas as contas, foco acessível e destino específico para pendência somente contábil.
Seleção preservada em revisão da mesma execução e limpa ao importar nova execução.
Verificação concluída: 33 testes passaram em Python 3.11, 3.12 e 3.13; o Chromium validou o atalho,
isolamento entre empresa/moeda/conta/direção, ativação pelo teclado, navegação de pendência somente contábil,
limpeza do recorte, preservação após revisão e limpeza ao importar nova execução.
CI: https://github.com/andrew-drew-beep/treasury-bridge-core/actions/runs/44825362758
Código validado: 0983c96116dd702265c05f13ee508dd788eade15. Captura do atalho inspecionada.

## Primeiro uso e instalação
README reorganizado com instruções para Windows, instalação de Python, download/extração do ZIP,
duplo clique em INICIAR_WINDOWS.bat, alternativa pelo terminal, encerramento, atualização com backup de var,
tabela de erros e instruções separadas para macOS/Linux e recursos opcionais.
Iniciador Windows adicionado com detecção de Python compatível, pasta de trabalho correta, abertura do navegador
e erros mantidos visíveis. Nova verificação windows-launcher no CI; resultado desta entrega aguardando CI.
