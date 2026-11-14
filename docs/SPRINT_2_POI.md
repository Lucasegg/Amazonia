# Sprint 2 — Pontos de interesse georreferenciados

## Objetivo

Adicionar referências reais de São Paulo ao mapa hexagonal sem revelar áreas que o personagem ainda não descobriu. Os POIs são pontos cartográficos; não afirmam que haverá comida, remédios, veículos, abrigo ou qualquer recurso disponível naquele local.

## Fonte dos dados

As coordenadas foram transcritas do Anexo I da Portaria SIURB nº 1/2019, publicação municipal que relaciona equipamentos e pontos de interesse com latitude e longitude:

https://legislacao.prefeitura.sp.gov.br/portaria-secretaria-municipal-de-infraestrutura-e-obras-siurb-1-de-11-de-janeiro-de-2019/anexo/5e14b3a91411926000a591fb/Anexo%20I%20da%20Portaria%20SIURB%20n%C2%BA%201_2019.pdf

A lista municipal de 240 pontos também foi consultada como referência complementar:

https://drive.prefeitura.sp.gov.br/cidade/secretarias/upload/240%20pontos%20edital.pdf

## Catálogo inicial

| Ponto | Latitude | Longitude | Célula axial |
|---|---:|---:|---:|
| Praça da Sé | -23.55037 | -46.63395 | 0:0 |
| Pátio do Colégio | -23.54807 | -46.63295 | 0:0 |
| Mercado Municipal | -23.54176 | -46.62939 | 0:1 |
| Parque Dom Pedro II | -23.545424 | -46.627899 | 0:1 |
| Parque da Luz | -23.53311 | -46.63558 | -2:3 |
| MASP | -23.56132 | -46.65586 | -2:-2 |
| Centro Cultural São Paulo | -23.57072 | -46.64025 | 1:-3 |
| Parque da Aclimação | -23.57256 | -46.62885 | 2:-3 |
| Parque da Independência | -23.58503 | -46.60973 | 5:-5 |

A atribuição a uma célula é calculada pela conversão geográfica para a grade axial do jogo. Pequenas diferenças entre o centro geométrico da célula e o ponto real são esperadas.

## Regra de visibilidade

- O personagem começa com a célula 0:0 descoberta.
- POIs de uma célula só são enviados pela API quando essa célula foi descoberta.
- Ao entrar em 0:1, Mercado Municipal e Parque Dom Pedro II passam a aparecer.
- O cliente não recebe os POIs escondidos e não decide o que está descoberto.
- Os marcadores aparecem no mapa e na lista de pontos conhecidos.

## Limites desta entrega

- POIs não são loot, recursos, zonas seguras ou serviços garantidos.
- Não há consulta de funcionamento atual, acesso, estado de conservação ou risco real.
- O catálogo é estático e mantido no código nesta fase; não exige nova tabela ou migração.
- A posição do jogador é fictícia e não há GPS.
- Coordenadas são referências cartográficas públicas; o posicionamento e a escala hexagonal são aproximações de protótipo.

## Próxima etapa

Criar interações específicas nos POIs e depois associar recursos e eventos ao estado do mundo, mantendo a descoberta e as consequências sob autoridade do servidor.
