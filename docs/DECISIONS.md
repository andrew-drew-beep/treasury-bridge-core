# Decisões de engenharia

| ID | Decisão | Motivo |
|---|---|---|
| D01 | Regras determinísticas primeiro | CNPJ, valor e contexto já fornecem evidência verificável |
| D02 | Decimal no domínio | Evitar erro de igualdade monetária por float |
| D03 | Dependência zero para CSV e interface | Recrutador executa sem chave, GPU ou instalação pesada |
| D04 | XLSX como extra opcional | Ler formato empresarial sem bloquear a demo mínima |
| D05 | Pareamento 1:1 exclusivo em ambos os lados | Evitar consumir o mesmo lançamento ou escolher pela ordem |
| D06 | Aprovação humana não altera a contabilidade | A PoC investiga e documenta, não faz baixas no ERP |
| D07 | Pendências bloqueiam grupo mesmo com diferença zero | Erros compensatórios não comprovam conciliação |
| D08 | SQLite para snapshots, revisão atual e eventos | Persistência local pequena e testável |
| D09 | Servidor restrito ao loopback | Não expor uma aplicação sem autenticação como serviço corporativo |
| D10 | Não adicionar IA/câmbio na v0.1 | Concluir primeiro o fluxo operacional e seus critérios de aceite |

## Segurança proporcional à demonstração
Consultas SQLite parametrizadas; escape de fórmulas em CSV; DOM com textContent; CSP sem scripts de terceiros;
origem e Host locais verificados; limite de requisição e comparação; sem caminhos de arquivo recebidos pela API;
sem postagem SAP, credenciais, dados de empresa ou downloads de modelo.
Não há hardening corporativo, isolamento de usuários, assinatura dos eventos, controle de retenção ou autenticação.
Uma revisão informa um nome, não prova identidade. Eventos são append-only pelo código da aplicação, editáveis no arquivo local.

## Evidência antes de expansão
Para introduzir IA, definir tarefa, conjunto de avaliação independente, taxa de erro e abstenção.
Modelo não pode mudar valor, CNPJ, conta nem selecionar fora dos candidatos admissíveis.
Mock não é IA. Não publicar métricas de produtividade da empresa sem medição.
Para câmbio, verificar fonte/cobertura das moedas, horários, dias úteis e custos negociados; PTAX não é taxa de contratação garantida.
