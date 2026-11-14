# Amazonia

RPG de sobrevivência e narrativa ambientado inicialmente na Grande São Paulo, com expansão planejada para os biomas e países da América do Sul.

## Estado do projeto

- Fase 0: visão, regras fundamentais e blueprint técnico documentados.
- Sprint 1: motor determinístico, API, campanhas, personagens e interface web inicial.
- Sprint 2: mapa interativo, grade hexagonal, movimentação validada e pipeline de POIs.
- A experiência é individual e textual; a IA será narradora, nunca autoridade sobre regras ou estado persistido.

## Estrutura

- docs/: design, regras, arquitetura, ambientes e fontes geográficas.
- apps/api/: API FastAPI, domínio, modelos SQLAlchemy, migrações Alembic e importador GeoJSON.
- apps/web/: React + TypeScript + Vite + MapLibre.
- .github/workflows/ci.yml: testes, migrações, auditoria e build.

## Ambientes

O desenvolvimento remoto deve usar o banco Neon de homologação descrito em docs/ambientes.md. DATABASE_URL é obrigatória e deve ser fornecida como variável de ambiente ou segredo. A API não cria banco local automaticamente. A CI usa SQLite isolado apenas para validar migrações e testes, sem acessar homologação ou produção.

Migrações devem ser revisadas e validadas primeiro em homologação. Não executar migrações automaticamente na inicialização da API.

## Executar a API

Requer Python 3.11 ou superior. Configure DATABASE_URL com a conexão do ambiente apropriado:

    cd apps/api
    pip install -e ".[dev]"
    alembic upgrade head
    uvicorn app.main:app --reload

## Executar a interface

    cd apps/web
    npm install
    npm run dev

Defina VITE_API_URL com a origem da API. Para permitir a interface no CORS, configure AMAZONIA_CORS_ORIGINS com a origem exata, por exemplo http://localhost:5173.

## Mapa e movimentação

O mapa de referência usa MapLibre GL JS e tiles raster do OpenStreetMap apenas durante o protótipo. A atribuição é exibida no mapa. Não há pré-carregamento em massa, nem garantia de disponibilidade ou uso ilimitado. Antes de publicar o jogo, será escolhido um provedor compatível com o volume esperado e seus termos.

A grade inicial usa hexágonos com raio de 500 metros. Cada movimento adjacente, validado no servidor, avança 10 minutos no relógio do mundo e registra a nova célula como descoberta. Células não descobertas não revelam terreno ou pontos de interesse.

A célula (0, 0) fica ancorada provisoriamente no centro geográfico aproximado de São Paulo (-23.5505, -46.6333). É apenas uma origem de teste do protótipo, não a localização narrativa definitiva. A aplicação não solicita GPS.

## Importar pontos de interesse

O catálogo aceita GeoJSON FeatureCollection com nome, categoria, coordenadas e identificador estável da fonte. Configure DATABASE_URL para a branch Neon de desenvolvimento, aplique as migrações e execute:

    cd apps/api
    python -m scripts.import_pois_geojson --input ../../data/pois.geojson

Nenhum POI real é inventado ou incluído por padrão. O processo de aquisição, fonte, licença e atribuição deve ser revisado antes da importação. A API só revela POIs associados a células já descobertas pelo personagem. Consulte docs/POI_DATA_PIPELINE.md.

## Testes

    cd apps/api
    pytest

    cd apps/web
    npm install
    npm run build

A CI executa testes e validação de migrações da API, auditoria de dependências frontend e build do frontend.

## Contas e campanhas privadas

A API usa sessão web em cookie HttpOnly, senha com Argon2id e campanhas vinculadas ao proprietário. O cookie de sessão é assinado HS256 e expira em 12 horas. Configure AMAZONIA_AUTH_SECRET com pelo menos 32 caracteres aleatórios no ambiente da API; nunca reutilize o segredo de CI.

Endpoints:
- POST /api/v1/auth/register
- POST /api/v1/auth/login
- POST /api/v1/auth/logout
- GET /api/v1/auth/me

O navegador recebe cookie de sessão HttpOnly e cookie CSRF separado. Requisições mutáveis com Origin exigem origem permitida e X-CSRF-Token. O logout incrementa session_version no banco e invalida todos os cookies emitidos anteriormente, inclusive cópias roubadas. Tentativas de login/cadastro têm limites persistidos no banco; e-mail e IP são armazenados somente como HMAC.

As migrações 0004 e 0005 criam contas, propriedade opcional de campanhas, versão de sessão e tabela de tentativas. Campanhas antigas sem proprietário não são atribuídas automaticamente.

**Limitação atual:** verificação de e-mail e recuperação de senha ainda dependem da integração e configuração de um provedor transacional de e-mail. Não considere o fluxo de conta pronto para produção até esses recursos, o teste com duas contas e a configuração segura da Vercel estarem concluídos.


### Verificação de e-mail e recuperação de senha

Em ambientes publicados, configure `AMAZONIA_REQUIRE_EMAIL_VERIFICATION=true`, `AMAZONIA_WEB_URL`, as variáveis SMTP e `AMAZONIA_OWNER_EMAIL` conforme `docs/deploy-vercel-neon.md`. Cadastro exige confirmação por link de uso único; recuperação expira em 30 minutos e revoga sessões antigas. O papel `owner` só é concedido após confirmação do e-mail configurado, nunca por endereço hardcoded.
