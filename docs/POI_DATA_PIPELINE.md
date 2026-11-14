# Pipeline de pontos de interesse (POIs)

## Objetivo

Importar locais reais de fontes públicas para o mapa sem consultar serviços externos a cada abertura do jogo e sem revelar locais ainda não descobertos.

## Formato de entrada

O importador aceita um GeoJSON FeatureCollection com geometria Point. Cada feature deve ter:
- geometry.coordinates: [longitude, latitude].
- properties.name: nome do local.
- properties.category: healthcare, police, fire_station, pharmacy, food, fuel, shelter, school, transport, market ou other.
- properties.source_ref: identificador estável e único na fonte (ex.: osm:node:123).
- properties.tags: tags públicas originais, quando disponíveis.

Pode incluir source, source_license e source_url. Para dados do OpenStreetMap, os padrões são OpenStreetMap, ODbL-1.0 e https://www.openstreetmap.org/.

## Importação

Com DATABASE_URL apontando para a branch Neon de desenvolvimento/homologação e migrações aplicadas:

    cd apps/api
    python -m scripts.import_pois_geojson --input ../../data/pois.geojson

O script faz upsert por source_ref. Não apaga POIs que não estejam no arquivo importado. Locais sem nome, fora da área de protótipo ou sem referência estável são ignorados; categorias desconhecidas e geometrias inválidas geram erro.

## Descoberta no jogo

- Cada POI é associado a uma célula hexagonal no momento da importação.
- A API retorna apenas POIs das células registradas em discovered_cells do personagem.
- Ao entrar em uma célula, os POIs nela passam a aparecer no mapa.
- O cliente não pode declarar POIs descobertos nem alterar as coordenadas.
- Os dados do mapa incluem a fonte e a licença de cada POI.

## Limites e governança

Nenhum POI real é embutido no código ou criado por suposição. Esta PR adiciona o esquema e o processo de importação, mas não carrega um conjunto de dados. A área e o arquivo de origem devem ser revisados antes da importação. Dados derivados do OpenStreetMap exigem atribuição e cumprimento da ODbL. O importador não baixa nem faz scraping; a aquisição do GeoJSON é uma etapa separada e auditável.
