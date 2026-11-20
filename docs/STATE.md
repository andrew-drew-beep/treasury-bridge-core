# Estado atual

Data de trabalho: 20 de novembro de 2026. Versão: 0.1.0.

## Implementado
Domínio com Decimal; três layouts CSV; XLSX opcional; motor 1:1 por CNPJ/valor/escopo/data/referência;
conferência separada de IN/OUT; relatórios por conta; exceções dos dois lados; revisão humana entre candidatos;
SQLite persistente; histórico; exportação CSV/JSON; interface web local; CLI; massa sintética de 12 contas;
33 testes automatizados e workflow CI Python 3.11–3.13.

## Verificação observada até este checkpoint
`python -m unittest discover -s tests -v`: 33 testes passaram em Python 3.12, incluindo XLSX.
CLI observada: 20 movimentos bancários, 19 contábeis, 15 sugestões por regra, 2 ambiguidades,
1 CNPJ ausente e 2 sem correspondência. A API foi testada para upload, revisão, exportação e recarga.
Validação visual em navegador ainda pendente: Chromium local não pôde iniciar no ambiente;
o navegador conectado não alcança o servidor loopback deste ambiente. Não declarar QA visual concluído.
Publicação em andamento em andrew-drew-beep/treasury-bridge-core. Não confundir workflow criado com CI remoto executado.

## Fora da versão
Integração SAP/bancos/PowerApps, dados reais, pagamentos parciais/agrupados, conversão cambial, IA/LLM,
previsões de câmbio, contas reais e autenticação corporativa.

## Próximo passo imediato
Concluir publicação/CI e atualizar currículo. Na próxima máquina, abrir a interface e conferir desktop/móvel,
filtros e aprovação; backend e seus contratos já possuem testes automatizados.
