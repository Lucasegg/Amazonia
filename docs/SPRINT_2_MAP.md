# Sprint 2 — Mapa de referência

## Escopo da entrega inicial

A PR do mapa adicionou a visualização cartográfica navegável da região inicial. Naquele momento, o centro era apenas uma referência e não definia o spawn. A etapa de exploração seguinte passou a definir um spawn fictício de teste na Praça da Sé e a alimentar o mapa com a posição persistida do personagem.

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
- A posição exibida é fictícia e vem do estado persistido da campanha.
- O mapa retorna e exibe somente pontos de interesse já descobertos pelo personagem.
- O catálogo inicial e as constantes provisórias estão documentados em docs/SPRINT_2_EXPLORATION.md.
