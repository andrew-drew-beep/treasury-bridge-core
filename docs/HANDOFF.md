# Retomada por outro modelo

## Comece aqui
1. Leia AGENTS.md, DISCOVERY.md, DECISIONS.md e STATE.md. O relato corrigiu a hipótese original: a importação banco→SAP já existe.
2. Execute `python -m unittest discover -s tests -v`.
3. Execute `python run.py demo`, depois `python run.py serve`; abra http://127.0.0.1:8765.
4. Siga o roteiro de três minutos no README. Compare o observado com STATE.md.

## Primeiro uso no Windows
O README começa pelo fluxo do usuário: Python compatível, ZIP completo extraído e INICIAR_WINDOWS.bat.
O .bat procura py -3 e python e mantém erros visíveis. scripts/start_windows.py verifica a versão e os arquivos,
usa a pasta raiz como diretório de trabalho, abre o servidor local e tenta abrir o navegador após vincular a porta.
Não instala dependências nem altera o esquema da base. A flag --check verifica ambiente sem abrir a interface.
O workflow windows-launcher inicia o programa em uma pasta com espaços e carrega a demonstração via HTTP.

## Navegação por pendência
Em Fechamento por conta, Há pendências → seleciona o escopo completo (empresa, conta bancária,
conta contábil, moeda, direção), ativa o filtro de pendências e leva o foco ao primeiro item.
Se só houver registros contábeis sem vínculo, o destino é essa lista.
Ver todas as contas limpa o escopo, mantendo o tipo de filtro escolhido. Nova execução limpa o escopo;
revisão na mesma execução preserva a seleção. Totais, exportações e regras continuam globais à execução.
O teste scripts/smoke_browser.py cobre isolamento por escopo, teclado e pendência somente contábil.

## Onde está cada responsabilidade
- `domain.py`: moedas, valores exatos, datas e transação normalizada.
- `ingest.py`: contratos explícitos CSV/XLSX, validação e origem de cada linha.
- `engine.py`: candidatos, exclusividade, decisões humanas e fechamento por grupo.
- `store.py`: snapshot determinístico, revisão atual e histórico SQLite transacional.
- `server.py`: API HTTP local e arquivos da interface em `src/treasury_bridge/web/`.
- `demo.py`: gerador reproduzível de dados fictícios.
- `export.py`: CSV com proteção contra interpretação como fórmula.
- `tests/`: casos de domínio, arquivo, revisão e API.

## Invariantes que não podem se perder na troca de contexto
1. Zero é diferença banco-contabilidade por grupo, não conta bancária zerada.
2. Entrada e saída não se compensam; conta, empresa e moeda não se misturam.
3. Totais iguais com itens não conciliados continuam pendentes.
4. Um lançamento contábil não atende a dois movimentos bancários.
5. CNPJ ausente/ambiguidade não autoriza adivinhação.
6. Aprovação registra um vínculo; não é baixa ou contabilização SAP.
7. A v0.1 usa regras, não IA. Não promover planos futuros a funcionalidades entregues.

## Limitações a preservar na comunicação
Não há extrato real, layout SAP real ou validação de produção. O período é o conjunto de arquivos selecionado.
Mapping de contas da demo é fictício. Janela é em dias corridos. Associação é 1:1.
Não há gabarito estatístico independente de um motor de IA, nem avaliação de ganho operacional real.
O banco SQLite não é inviolável. Não hospedar publicamente sem projeto de autenticação, isolamento e retenção.

## Próximas evoluções propostas
P1: configuração de mapping por banco/empresa e período de corte explícito na interface.
P2: fluxo para registrar evidência adicional quando CNPJ está ausente, sem inventar vínculo.
P3: avaliar agrupamentos/parciais com regras e massa adversarial separada.
P4: experimentar IA somente para investigação de exceções; medir erro e abstenção.
P5: módulo cambial independente, com fontes/horários e simulação de exposição.

## Texto de currículo permitido após validação
Treasury Bridge — PoC em Python para conferência bancária e contábil com dados sintéticos,
comparação por CNPJ, valores exatos, tratamento de ambiguidades e revisão com histórico.
Não escrever "integrei o SAP", "implantei na empresa", "prevejo câmbio" ou "reduzi X% do tempo".
