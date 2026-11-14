# Amazonia

RPG de sobrevivência e narrativa ambientado inicialmente na Grande São Paulo, com expansão planejada para os biomas e países da América do Sul.

## Estado do projeto

- Fase 0: visão, regras fundamentais e blueprint técnico documentados.
- Sprint 1: motor determinístico, API, campanhas e personagens persistidos.
- Interface web inicial para criar campanha e ficha.
- A IA será narradora; não controla dados, atributos, inventário ou estado persistido.

## Estrutura

- docs/: design, regras e arquitetura.
- apps/api/: FastAPI, domínio, modelos SQLAlchemy e migrações Alembic.
- apps/web/: React + TypeScript + Vite.
- .github/workflows/ci.yml: testes e builds.

## Ambientes

O desenvolvimento remoto deve usar o banco Neon de homologação descrito em docs/ambientes.md. DATABASE_URL é obrigatória e deve ser fornecida como variável de ambiente/segredo; nunca inclua credenciais no repositório. A CI usa SQLite isolado apenas para validar migrações e testes, sem acessar homologação ou produção.

A migração deve ser revisada e validada primeiro em homologação. Não executar migrações automaticamente na inicialização da API.

## Executar a API

Requer Python 3.11 ou superior. Configure DATABASE_URL com a conexão do ambiente apropriado antes de iniciar:

    cd apps/api
    pip install -e ".[dev]"
    alembic upgrade head
    uvicorn app.main:app --reload

## Executar a interface

    cd apps/web
    npm install
    npm run dev

Defina VITE_API_URL com a origem da API. Em desenvolvimento local, o padrão é http://localhost:8000; em ambiente remoto, use a URL HTTPS do serviço de API.

## Testes

    cd apps/api
    pytest

A CI executa testes e validação de migrações da API, além de typecheck e build do frontend.
