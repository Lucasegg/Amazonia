# Amazonia

RPG de sobrevivência e narrativa ambientado inicialmente na Grande São Paulo, com expansão planejada para os biomas e países da América do Sul.

## Estado do projeto

- Fase 0: visão, regras fundamentais e blueprint técnico documentados.
- Sprint 1: motor determinístico, API e persistência inicial de campanhas/personagens.
- Experiência inicial: campanha individual, mapa 2D e narrativa textual.
- A IA será narradora; não controla dados, atributos, inventário ou estado persistido.

## Estrutura

- `docs/`: design, regras e arquitetura.
- `apps/api/`: API FastAPI, domínio, modelos SQLAlchemy e migrações Alembic.
- `.github/workflows/ci.yml`: testes e validação da migração.

## Executar a API localmente

Requer Python 3.11 ou superior.

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

A configuração padrão usa SQLite local para facilitar o início. Para PostgreSQL, defina `DATABASE_URL` antes de executar a migração. Nenhum banco remoto é provisionado por esta PR.

A documentação interativa fica em `http://127.0.0.1:8000/docs`.

## Executar os testes

```bash
cd apps/api
pytest
```

## Rotas iniciais

- `GET /health`
- `GET /api/v1/game/origins`
- `GET /api/v1/game/origins/{origin_id}`
- `POST /api/v1/game/checks`
- `POST /api/v1/campaigns`
- `GET /api/v1/campaigns/{campaign_id}`
- `POST /api/v1/campaigns/{campaign_id}/character`

Cada campanha aceita um personagem no primeiro fluxo do protótipo. As regras e os valores iniciais permanecem versionados nos documentos de design. A Sprint 1 não conecta provedor de IA nem serviço remoto pago.
