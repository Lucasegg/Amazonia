# Sprint 2 — Grade hexagonal e movimentação

## Escopo desta entrega

A movimentação usa uma grade hexagonal axial persistida no personagem. A posição inicial do protótipo é a célula (0, 0), ancorada provisoriamente no centro geográfico aproximado de São Paulo (-23.5505, -46.6333). Esse ponto é uma referência de teste, não uma decisão narrativa definitiva.

## Geometria

- Raio geométrico de cada hexágono: 500 metros.
- Distância entre centros de células adjacentes: aproximadamente 866 metros.
- Coordenadas axiais q/r, com distância calculada pelo máximo entre |dq|, |dr| e |dq + dr|.
- O mapa mostra a célula atual, células descobertas e células adjacentes possíveis.
- Células ainda não descobertas não revelam terreno, eventos ou pontos de interesse.

## Movimento

- O cliente envia somente a célula de destino.
- O servidor valida campanha, personagem, limites e adjacência.
- Um movimento válido avança o relógio do mundo em 10 minutos.
- A nova célula é registrada como descoberta e a posição é persistida.
- Movimento para a mesma célula retorna conflito; salto de células é rejeitado.
- Não há ainda custo de fadiga, combate, veículos ou bloqueios de terreno.

## Pontos de interesse georreferenciados

- O catálogo inicial usa coordenadas de referências públicas municipais de São Paulo.
- Cada POI é convertido para a célula axial mais próxima.
- O mapa e a API retornam POIs somente quando a célula correspondente está descoberta.
- Os pontos são referências cartográficas, não promessa de recursos, serviços, segurança ou disponibilidade.
- O catálogo é estático nesta fase e não exige migração de banco.

Consulte docs/SPRINT_2_POI.md para as fontes, coordenadas e regras de visibilidade.

## Integridade

A posição e as descobertas são persistidas no banco. O cliente não escolhe tempo decorrido, não declara uma célula como descoberta e não pode mover mais de uma célula por ação. A grade é uma aproximação de protótipo; antes de uso público, será validada contra a malha geográfica e as fontes oficiais escolhidas.

## Próximas etapas

- Associar recursos e eventos do mundo a POIs sem presumir disponibilidade real.
- Definir terreno, obstáculos e custos de movimento por tipo de terreno.
- Integrar descoberta progressiva com a narrativa e os eventos do mundo.
- Escolher a posição inicial narrativa definitiva.
