# Amazonia

RPG de sobrevivência e narrativa ambientado inicialmente na Grande São Paulo, com expansão planejada para os biomas e países da América do Sul.

## Estado do projeto

- Fase 0: visão, regras fundamentais e blueprint técnico documentados.
- Sprint 1: fundação do motor determinístico e API inicial em implementação.
- Experiência inicial: campanha individual, mapa 2D e narrativa textual.
- A IA será narradora; não controla dados, atributos, inventário ou estado persistido.

## Estrutura

- `docs/`: design, regras e arquitetura.
- `apps/api/`: API FastAPI e domínio do jogo.
- `.github/workflows/ci.yml`: testes automatizados da API.

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
uvicorn app.main:app --reload
```

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

As regras e os valores iniciais permanecem versionados nos documentos de design. A Sprint 1 não conecta provedor de IA nem serviço remoto pago.
