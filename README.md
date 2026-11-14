# Amazonia

RPG de sobrevivência e narrativa ambientado inicialmente na Grande São Paulo, com expansão planejada para os biomas e países da América do Sul.

## Estado do projeto

- Fase 0: visão, regras fundamentais e blueprint técnico documentados.
- Sprint 1: motor determinístico, API, campanhas, personagens e interface web inicial.
- Sprint 2: mapa interativo, pontos de interesse reais, descoberta progressiva, deslocamento e histórico de eventos.
- A experiência é individual e textual; a IA será narradora, nunca autoridade sobre regras ou estado persistido.

## Estrutura

- docs/: design, regras, arquitetura e ambientes.
- apps/api/: API FastAPI, domínio, modelos SQLAlchemy e migrações Alembic.
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

## Mapa e dados cartográficos

O mapa usa MapLibre GL JS e tiles raster do OpenStreetMap durante o protótipo. A atribuição é exibida no mapa. Não há pré-carregamento em massa nem garantia de disponibilidade ou uso ilimitado. Antes de publicar o jogo, será escolhido um provedor compatível com o volume esperado e seus termos.

O personagem começa em uma posição fictícia de teste na Praça da Sé, no Centro de São Paulo. O mapa revela somente pontos descobertos. A aplicação não solicita GPS nem coleta a localização real do jogador. As coordenadas e regras provisórias estão documentadas em docs/SPRINT_2_EXPLORATION.md.

## API de exploração

- GET /api/v1/campaigns/{campaign_id}/map
- POST /api/v1/campaigns/{campaign_id}/actions
- GET /api/v1/campaigns/{campaign_id}/events

As ações search e move são validadas no servidor e registradas com chave de idempotência. Os parâmetros de raio, tempo de busca e velocidade de caminhada ainda são provisórios.

## Testes

    cd apps/api
    pytest

    cd apps/web
    npm install
    npm run build

A CI executa testes e validação de migrações da API, auditoria de dependências frontend e build do frontend.
