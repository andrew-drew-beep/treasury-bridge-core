# Mapeamento da descoberta

## Objetivo
Demonstrar a passagem de uma dor operacional para regras verificáveis em uma prova de conceito independente.
Fonte: relato fornecido pelo autor do projeto durante uma entrevista conversacional. Não houve acesso a sistemas corporativos.
Este documento registra o entendimento relatado, não uma auditoria do ambiente.

## Processo relatado
1. Extratos chegam automaticamente a uma pasta chamada repositório.
2. O SAP recebe o conteúdo e realiza algumas contabilizações automáticas de entradas e saídas.
3. A equipe confere banco e contabilidade; entradas e saídas usam contas contábeis separadas.
4. Valores iguais são diferenciados comparando o CNPJ da contraparte.
5. Fechar a conferência significa zerar as diferenças entre movimentações e contabilizações correspondentes.

Outros elementos relatados: 12 contas bancárias; consultas em diferentes ambientes/relatórios SAP; PowerApps em solicitações
e lançamentos; conferência diária de saldos; trabalho manual remanescente. Não se conhece a quantidade de bancos ou layouts.

## Correções em relação à hipótese inicial
- Já existe ponte de importação: não reconstruir integração banco→ERP como justificativa do projeto.
- Doze contas não significam doze layouts.
- CNPJ é evidência concreta; texto sem informação não permite inventar contraparte.
- Zero de conciliação não é saldo bancário zero, nem entrada menos saída zero.
- Contabilizar e conciliar são conceitos distintos.
- Códigos contábeis mencionados informalmente não foram validados e não entram na demonstração.

## Necessidade cambial relatada
Pagamentos internacionais em USD, EUR, CNY, JPY e GBP; fechamento semanal e intercompanhias no dia 15;
acompanhamento de mercado e interesse em expectativas de câmbio. É uma frente futura.
Referências históricas, projeções externas e simulações devem manter fontes, datas e horizontes distintos.
Não inferir uma previsão semanal a partir de expectativas anuais. Nenhuma recomendação financeira é implementada.

## Decisões de demonstração, ainda não validadas no ambiente real
- Comparação 1:1 por CNPJ+valor+contexto+janela de dois dias corridos, ajustável.
- Contas fictícias DEMO_RECEIPTS e DEMO_PAYMENTS; a relação real conta/direção depende de configuração futura.
- O relatório de entrada é um contrato nosso com registros POSTED, não exportação SAP certificada.
- Um par com referência em apenas um dos lados pode ser sugerido por regra se exclusivo, exigindo revisão humana.
- Apenas candidatos compatíveis podem receber aprovação; casos sem evidência permanecem abertos.

## Pontos para uma descoberta futura
Nome e colunas do relatório SAP; identificador único estável; semântica das datas; política de arredondamento;
período de corte; contas transitórias; pagamentos agrupados/parciais; estornos; tarifas; indicadores de importação;
ação humana final no SAP/PowerApps; volume e tempo por etapa; disponibilidade do CNPJ por fonte.
Nenhuma dessas lacunas impede uma demonstração sintética, mas impede alegar compatibilidade ou prontidão de produção.

## Aceite funcional
A demo abre sem API externa, importa layouts fictícios, separa contas e sentidos, calcula diferenças exatas,
não faz associações ambíguas, não reutiliza registros, registra revisão, exporta pendências e preserva histórico.
Cada regra tem casos de teste positivos e negativos. Zero de totais com itens errados deve continuar pendente.
