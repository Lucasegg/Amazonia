# Sprint 2 — Mapa de referência

## Escopo desta entrega

Esta etapa adiciona somente a visualização cartográfica navegável da região inicial. O mapa não define spawn, não move o personagem e não revela pontos de interesse do jogo. O centro visual é uma referência geográfica aproximada da cidade de São Paulo: longitude -46.6333, latitude -23.5505.

## Tecnologia e dados

- MapLibre GL JS é a biblioteca de renderização cartográfica, licenciada sob BSD-3-Clause.
- O protótipo usa tiles raster do OpenStreetMap e mantém a atribuição visível no próprio mapa.
- O servidor público de tiles é utilizado apenas para desenvolvimento e avaliação de baixo volume. Não fazer pré-carregamento em massa, scraping, uso offline ou assumir disponibilidade/serviço ilimitado.
- Antes de publicar ou ampliar usuários, escolher um provedor de tiles compatível com o volume esperado e seus termos.

Referências:
- MapLibre GL JS: https://maplibre.org/maplibre-gl-js/docs/
- Política de tiles do OpenStreetMap: https://operations.osmfoundation.org/policies/tiles/

## Privacidade e integridade do mundo

- O navegador não solicita GPS nem transmite a localização real do jogador.
- O centro do mapa é apenas uma referência visual; não representa a posição de nenhum personagem.
- Posição inicial, POIs, fog of war, movimento e descoberta serão definidos pelo estado persistido do jogo em uma etapa posterior.

## Próxima fatia

Adicionar catálogo de pontos de interesse com coordenadas de fontes públicas verificáveis, posição inicial fictícia do personagem, descoberta progressiva e movimentação validada no servidor. O mapa só exibirá marcadores conhecidos pelo personagem.
