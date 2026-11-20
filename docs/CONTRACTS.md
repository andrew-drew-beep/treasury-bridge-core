# Contratos de entrada e saída

CSV UTF-8, com delimitador `;` ou `,` identificado pelo cabeçalho. Datas `AAAA-MM-DD` ou `DD/MM/AAAA`.
Valor positivo no contrato canônico; direção IN/OUT. No beta o sinal define a direção.
Valores brasileiros com vírgula decimal podem usar ponto de milhar. Com ponto decimal, não usar vírgula de milhar.
Rejeitar casas excedentes; BRL/USD/EUR/GBP/CNY usam duas, JPY zero. Não converter moedas ou arredondar silenciosamente.

## Esquema canônico
Obrigatórios: `id, company, bank_account, currency, direction, date, amount, cnpj`.
`cnpj` pode ser vazio, mas o item fica sem associação automática.
Opcionais: `ledger_account, reference, description`.
Para o lado contábil também são obrigatórios `ledger_account` e `posting_status=POSTED`.
IDs precisam ser únicos em todo o lote de cada lado. Itens com o mesmo ID em dois arquivos rejeitam o lote inteiro.
Banco e contabilidade têm namespaces de ID separados. Sistemas reais precisariam construir essa chave de forma explícita.

Agrupamento: empresa + conta bancária + conta contábil + moeda + direção. O período é o conjunto completo de arquivos
enviado pelo usuário; não há filtro de período escondido. Selecionar extrato e razão do mesmo intervalo de conferência.
Datas mínima/máxima ficam nos registros e no JSON. O corte e a janela são decisões explícitas do operador.

Na ausência de ledger_account no banco: IN→DEMO_RECEIPTS, OUT→DEMO_PAYMENTS.
No contrato canônico é possível fornecer outras contas explicitamente. A configuração por banco é evolução futura.

## Banco alpha
`ID;Empresa;Conta;Moeda;Tipo;Data;Valor;CNPJ;Documento;Historico`
Tipos: ENTRADA, SAIDA ou SAÍDA. Documento e Historico são opcionais.

## Banco beta
`transaction_id,company,account,currency,booking_date,signed_amount,tax_id,reference,description`
Positivo=IN; negativo=OUT. Zero é recusado. Reference e description são opcionais.

## XLSX opcional
Mesmo cabeçalho dos CSV; primeira planilha, primeira linha como cabeçalho. Sem fórmulas.
Identificadores fiscais devem ser texto para preservar zeros. Valores numéricos são convertidos com Decimal(str(valor));
a planilha já pode ter perdido precisão antes de chegar à aplicação. Não usar para dados monetários além da precisão do Excel.
O identificador é normalizado preservando letras e zeros, removendo apenas pontuação de apresentação.
Há validação estrutural de 14 caracteres alfanuméricos, mas não verificação fiscal/dígitos verificadores.
DEMO0000000001 e similares são marcadores fictícios, não CNPJs cadastrados.

## Saídas
JSON: transações normalizadas, fonte/linha, grupos, diferenças, estados e candidatos.
JSON da interface também inclui eventos de revisão. CLI não mantém revisão ou banco SQLite.
CSV: uma linha por movimento bancário e linhas LEDGER_UNMATCHED para registros contábeis restantes.
Texto com prefixo de fórmula é neutralizado para abertura em planilhas.
Valores monetários são strings decimais; exibição visual usa formatação, cálculos são sempre feitos no servidor.

## Identidade de execução
Hash SHA-256 truncado dos dados normalizados, origem/linha, ordem, janela e versão da regra.
Mesmos arquivos em mesma ordem geram o mesmo run_id e preservam revisões.
Reordenar arquivos/linhas, renomear origem ou mudar regras gera nova execução; não é deduplicação semântica global.
Duplicações com IDs distintos não são removidas: passam pelo grafo e podem gerar ambiguidades.
