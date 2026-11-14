# Sprint 3 — Inventário e consumíveis

## Objetivo
Fechar o primeiro ciclo de preparação e recuperação de necessidades do personagem, mantendo o inventário persistido na campanha.

## Itens iniciais
Todas as três origens do protótipo começam com:
- 1 unidade de água potável;
- 1 unidade de ração de emergência;
- os equipamentos específicos da origem.

## Regras iniciais de consumo
- Água potável reduz sede em 25 pontos.
- Ração de emergência reduz fome em 20 pontos.
- Indicadores nunca ficam abaixo de zero.
- Cada consumo avança o relógio do mundo em 5 minutos.
- O item é removido do inventário após o consumo.
- O servidor valida a existência e o tipo do item; o cliente não determina efeitos.
- Requisições com item desconhecido ou ausente são rejeitadas sem alterar personagem ou relógio.

## Persistência e compatibilidade
O inventário existente já é uma coluna JSON com identificadores de itens. A entrega mantém esse formato e não exige migração de banco. Itens de equipamento permanecem no inventário e não podem ser consumidos por esta rota.

## Fora do escopo
- Coleta de recursos no mapa.
- Peso, volume, durabilidade ou deterioração.
- Água contaminada, preparo de alimentos ou doenças.
- Penalidades de saúde por fome/sede.
- Recuperação de fadiga por descanso.
- Balanceamento definitivo das quantidades e custos de tempo.

Os valores são parâmetros provisórios de jogo, não recomendações médicas ou nutricionais.
