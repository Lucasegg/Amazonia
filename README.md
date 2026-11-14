# Amazonia

RPG de sobrevivência e narrativa ambientado inicialmente na Grande São Paulo, com expansão planejada para os biomas e países da América do Sul.

## Estado do projeto

- Fase 0: visão, regras fundamentais e blueprint técnico documentados.
- Sprint 1: motor determinístico, API, campanhas, personagens e interface web inicial.
- Experiência individual com narrativa textual; mapa interativo e simulação de mundo entram nas próximas etapas.
- A IA será narradora; não controla dados, atributos, inventário ou estado persistido.

## Estrutura

- docs/: design, regras, arquitetura e ambientes.
- apps/api/: API FastAPI, domínio, modelos SQLAlchemy e migrações Alembic.
- apps/web/: React + TypeScript + Vite.
- .github/workflows/ci.yml: testes, migrações e build.

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

## Testes

    cd apps/api
    pytest

A CI executa testes e validação de migrações da API, além do build do frontend.
