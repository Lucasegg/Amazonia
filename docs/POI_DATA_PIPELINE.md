# Pipeline de pontos de interesse (POIs)

## Objetivo

Importar locais reais de fontes públicas para o mapa sem consultar serviços externos a cada abertura do jogo e sem revelar locais ainda não descobertos.

## Formato de entrada

O importador aceita um GeoJSON FeatureCollection com geometria Point. Cada feature deve ter:
- geometry.coordinates: [longitude, latitude].
- properties.name: nome do local.
- properties.category: healthcare, police, fire_station, pharmacy, food, fuel, shelter, school, transport, market ou other.
- properties.source_ref: identificador estável e único na fonte (ex.: osm:node:123).
- properties.source: nome da fonte.
- properties.source_license: licença exata da fonte.
- properties.source_url: URL HTTP/HTTPS da página do conjunto de dados ou do registro de origem.
- properties.tags: tags públicas originais, quando disponíveis.

O importador só aplica padrões quando source_ref identifica claramente um elemento OSM (osm:node:id, osm:way:id ou osm:relation:id). Nesse caso, source é OpenStreetMap, source_license é ODbL-1.0 e source_url aponta para o elemento específico. Para qualquer outra fonte, origem, licença e URL são obrigatórias. Isso evita atribuir ODbL incorretamente a dados de terceiros.

## Fontes documentadas

### OpenStreetMap

- Fonte: OpenStreetMap.
- Licença: ODbL-1.0.
- Atribuição: © OpenStreetMap contributors.
- URL de referência: https://www.openstreetmap.org/
- Cada registro deve preservar o tipo e o ID do elemento OSM.

### GeoSampa — Prefeitura de São Paulo

- A página oficial de licença do GeoSampa informa que os dados geoespaciais são disponibilizados sob Creative Commons Attribution-ShareAlike 4.0 (CC BY-SA 4.0): https://prefeitura.sp.gov.br/web/licenciamento/w/licen%C3%A7a-para-uso-de-dados-do-geosampa
- Exemplo de metadado: UBS/Posto/Centro de Saúde, camada vetorial do tipo Point, com revisão em 18/06/2025 e manutenção anual: https://metadados.geosampa.prefeitura.sp.gov.br/geonetwork/srv/api/records/bc44ee6c-e973-4670-b912-9ac8d64b9f56
- Para dados GeoSampa, cada feature deve declarar source=GeoSampa, source_license=CC-BY-SA-4.0 e source_url apontando para o registro/camada utilizado.
- Não aplicar o padrão ODbL a dados GeoSampa.

A camada de UBS/Posto/Centro de Saúde inclui estabelecimentos municipais, estaduais, federais e privados. A camada deve ser tratada como referência geográfica; não confirma funcionamento atual, disponibilidade de atendimento ou estoque.

## Importação

Com DATABASE_URL apontando para a branch Neon de desenvolvimento/homologação e migrações aplicadas:

    cd apps/api
    python -m scripts.import_pois_geojson --input ../../data/pois.geojson

O script faz upsert por source_ref. Não apaga POIs que não estejam no arquivo importado. Locais sem nome ou fora da área de protótipo são ignorados; categorias desconhecidas, geometrias inválidas, referências instáveis, URLs inválidas e metadados de licença ausentes geram erro.

## Descoberta no jogo

- Cada POI é associado a uma célula hexagonal no momento da importação.
- A API retorna apenas POIs das células registradas em discovered_cells do personagem.
- Ao entrar em uma célula, os POIs nela passam a aparecer no mapa.
- O cliente não pode declarar POIs descobertos nem alterar as coordenadas.
- Os dados do mapa incluem a fonte e a licença de cada POI.

## Limites e governança

Nenhum POI real está embutido no código ou foi criado por suposição. O pipeline não baixa nem faz scraping; a aquisição do GeoJSON é uma etapa separada e auditável. Antes da importação, revisar área geográfica, data de atualização, campos, licença e atribuição. Não tratar a presença de um POI como confirmação de recursos, serviços, segurança ou disponibilidade no mundo do jogo.
