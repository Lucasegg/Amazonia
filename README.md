# Amazonia

RPG de sobrevivência e narrativa ambientado inicialmente na Grande São Paulo, com expansão planejada para os biomas e países da América do Sul.

## Estado do projeto

- Fase 0: visão, regras fundamentais e blueprint técnico documentados.
- Sprint 1: motor determinístico, API, persistência inicial e interface de criação de campanha/personagem.
- Experiência inicial: campanha individual, mapa 2D e narrativa textual.
- A IA será narradora; não controla dados, atributos, inventário ou estado persistido.

## Estrutura

- `docs/`: design, regras e arquitetura.
- `apps/api/`: API FastAPI, domínio, modelos SQLAlchemy e migrações Alembic.
- `apps/web/`: interface React + TypeScript + Vite.
- `.github/workflows/ci.yml`: testes, migrações e build da interface.

## Executar localmente

Requer Python 3.11+ e Node.js 22+.

**Terminal 1 — API**

```bash
cd apps/api
python -m venv .venv
# Windows PowerShell:
.venv\\Scripts\\Activate.ps1
# Linux/macOS:
# source .venv/bin/activate
pip install -e ".[dev]"
alembic upgrade head
uvicorn app.main:app --reload
```

A API e sua documentação ficam em `http://127.0.0.1:8000` e `http://127.0.0.1:8000/docs`.

**Terminal 2 — Interface**

```bash
cd apps/web
npm install
npm run dev
```

A interface fica em `http://localhost:5173`. Se a API estiver em outro endereço, configure `VITE_API_URL` com a URL base da API. Para ajustar origens permitidas no backend, configure `AMAZONIA_CORS_ORIGINS` com uma lista separada por vírgulas.

O banco padrão é SQLite local. PostgreSQL pode ser usado por meio de `DATABASE_URL`. Nenhum serviço remoto é provisionado automaticamente.

## Testes e build

```bash
cd apps/api
pytest
```

```bash
cd apps/web
npm install
npm run build
```

## Rotas iniciais

- `GET /health`
- `GET /api/v1/game/origins`
- `GET /api/v1/game/origins/{origin_id}`
- `POST /api/v1/game/checks`
- `POST /api/v1/campaigns`
- `GET /api/v1/campaigns/{campaign_id}`
- `POST /api/v1/campaigns/{campaign_id}/character`

O mapa interativo, movimentação, exploração e integração de IA ainda serão implementados nas próximas etapas.
