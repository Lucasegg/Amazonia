# Amazonia — Sprint 1: Fundação

**Status:** implementação inicial em revisão; nenhum ambiente remoto foi provisionado.

## Entregas

- Frontend React + TypeScript + Vite.
- API FastAPI e domínio isolado em módulo próprio.
- Catálogo das três origens iniciais com habilidades, equipamentos e vantagens contextuais.
- Motor D20 com atributos, níveis de habilidade, dificuldade e modificadores; rolagem gerada no servidor.
- Criação e consulta de campanhas persistidas em PostgreSQL por SQLAlchemy.
- Migração Alembic versionada para a tabela inicial de campanhas.
- Testes unitários do domínio e testes HTTP com SQLite em memória.
- CI para testes, lint e compilação da API, typecheck e build do frontend.
- Tela inicial para criar campanha e visualizar ficha e equipamentos.

## Segurança e ambientes

- DATABASE_URL é obrigatória; não há fallback silencioso para banco local na API.
- Testes usam SQLite em memória e não acessam homologação ou produção.
- Migração deve ser aplicada primeiro em homologação, conforme docs/ambientes.md.
- Nenhuma credencial, banco remoto, serviço pago ou deploy foi criado.
- Não há login, multiplayer, IA narradora, GPS ou tiles externos nesta sprint.

## Limitações

- Ainda não há autenticação nem isolamento multiusuário; não publicar API aberta.
- Ainda não há fluxo de ações persistidas, inventário dinâmico, mapa ou eventos.
- Os atributos iniciais são todos 3; balanceamento e distribuição de pontos ficam para a próxima iteração.
- A interface é uma primeira tela funcional, não a interface final do jogo.
- CI não aplica migrações nem faz deploy.
