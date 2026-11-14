# Pipeline de pontos de interesse (POIs)

## Objetivo

Importar locais reais de fontes públicas para o mapa sem consultar serviços externos a cada abertura do jogo e sem revelar locais ainda não descobertos.

## Formato de entrada

O importador aceita um GeoJSON FeatureCollection com geometria Point. Cada feature deve ter:
- geometry.coordinates: [longitude, latitude].
- properties.name: nome do local.
- properties.category: healthcare, police, fire_station, pharmacy, food, fuel, shelter, school, transport, market, water, park ou other.
- properties.source_ref: identificador estável e único na fonte (ex.: osm:node:123).
- properties.source: nome da fonte.
- properties.source_license: licença exata da fonte.
- properties.source_url: URL HTTP/HTTPS da página do conjunto de dados ou do registro de origem.
- properties.tags: tags públicas originais, quando disponíveis.

O importador só aplica padrões quando source_ref identifica claramente um elemento OSM (osm:node:id, osm:way:id ou osm:relation:id). Nesse caso, source é OpenStreetMap, source_license é ODbL-1.0 e source_url aponta para o elemento específico. Para qualquer outra fonte, origem, licença e URL são obrigatórias. Isso evita atribuir ODbL incorretamente a dados de terceiros.

## Extração OpenStreetMap

O script download_osm_pois faz uma única consulta limitada à região inicial (raio padrão de 5 km ao redor do Centro de São Paulo) e grava um GeoJSON local:

    cd apps/api
    python -m scripts.download_osm_pois --output ../../data/pois.geojson

O raio e o centro podem ser ajustados por argumentos. A consulta inclui serviços de saúde, polícia, bombeiros, farmácias, água potável, alimentação, combustível, abrigos, escolas, transporte, mercados e parques. O script preserva IDs OSM, tags, links de cada elemento e atribuição/licença ODbL-1.0.

O download é manual, serial e de uso pontual. Não executar na inicialização do jogo, não agendar consultas recorrentes e não disparar várias consultas em paralelo. A instância pública Overpass é um serviço comunitário sem SLA; pode estar sobrecarregada e impor limites. O script identifica a aplicação por User-Agent e não faz retry automático em caso de erro/limite. Consulte a política e o estado do serviço antes de novas extrações:
- https://wiki.openstreetmap.org/wiki/Overpass_API
- https://overpass.ch/guides/overpass-api-errors

Depois de revisar o GeoJSON e os metadados, importe para a branch Neon de desenvolvimento/homologação:

    python -m scripts.import_pois_geojson --input ../../data/pois.geojson

A extração local não é commitada automaticamente no repositório. O arquivo pode conter muitos pontos e deve ser revisado antes de qualquer importação.

## Fontes documentadas

### OpenStreetMap

- Fonte: OpenStreetMap.
- Licença: ODbL-1.0.
- Atribuição: © OpenStreetMap contributors.
- URL de referência: https://www.openstreetmap.org/
- Cada registro preserva o tipo e o ID do elemento OSM.
- A licença e as regras de atribuição oficiais: https://www.openstreetmap.org/copyright

### GeoSampa — Prefeitura de São Paulo

- A página oficial de licença do GeoSampa informa que os dados geoespaciais são disponibilizados sob Creative Commons Attribution-ShareAlike 4.0 (CC BY-SA 4.0): https://prefeitura.sp.gov.br/web/licenciamento/w/licen%C3%A7a-para-uso-de-dados-do-geosampa
- Exemplo de metadado: UBS/Posto/Centro de Saúde, camada vetorial do tipo Point, com revisão em 18/06/2025 e manutenção anual: https://metadados.geosampa.prefeitura.sp.gov.br/geonetwork/srv/api/records/bc44ee6c-e973-4670-b912-9ac8d64b9f56
- Para dados GeoSampa, cada feature deve declarar source=GeoSampa, source_license=CC-BY-SA-4.0 e source_url apontando para o registro/camada utilizado.
- Não aplicar o padrão ODbL a dados GeoSampa.

A camada de UBS/Posto/Centro de Saúde inclui estabelecimentos municipais, estaduais, federais e privados. A camada deve ser tratada como referência geográfica; não confirma funcionamento atual, disponibilidade de atendimento ou estoque.

## Descoberta no jogo

- Cada POI é associado a uma célula hexagonal no momento da importação.
- A API retorna apenas POIs das células registradas em discovered_cells do personagem.
- Ao entrar em uma célula, os POIs nela passam a aparecer no mapa.
- O cliente não pode declarar POIs descobertos nem alterar as coordenadas.
- Os dados do mapa incluem a fonte e a licença de cada POI.

## Limites e governança

O downloader gera um arquivo local; não grava diretamente no banco. O importador faz upsert por source_ref e não apaga POIs ausentes no arquivo. Locais sem nome ou fora da área do protótipo são ignorados; categorias desconhecidas, geometrias inválidas, referências instáveis, URLs inválidas e metadados de licença ausentes geram erro.

Nenhum POI real foi importado automaticamente nesta etapa. Antes da importação, revisar área geográfica, data de atualização, campos, licença e atribuição. Não tratar a presença de um POI como confirmação de recursos, serviços, segurança ou disponibilidade no mundo do jogo.
