# Deploy Amazonia na Vercel e conectar ao Neon

Este repositório é um monorepo com dois projetos Vercel independentes:
- API: diretório raiz `apps/api`
- Web: diretório raiz `apps/web`

Os previews da PR de autenticação foram reconhecidos pelo bot da Vercel. A marcação `Ready` confirma o build/deployment, mas não substitui os testes HTTP de ponta a ponta.

## Variáveis da API

Configure no projeto Vercel `api`:

| Variável | Preview | Produção |
| --- | --- | --- |
| `DATABASE_URL` | URL pooled do banco Neon `amazonia` no ambiente de homologação | URL pooled do banco Neon de produção |
| `AMAZONIA_AUTH_SECRET` | Segredo aleatório exclusivo, mínimo 32 caracteres | Outro segredo aleatório exclusivo |
| `AMAZONIA_CORS_ORIGINS` | URL exata do preview Web, sem barra final | Domínio definitivo do Web |
| `AMAZONIA_COOKIE_SECURE` | `true` | `true` |
| `AMAZONIA_COOKIE_SAMESITE` | `none` para Web/API em hosts Vercel distintos | `none` se Web/API permanecerem em sites distintos; `lax` se estiverem sob o mesmo site |

Gere um segredo localmente com `openssl rand -hex 32`. Não reutilize o segredo da CI, não o coloque no Git e não o envie em mensagens. Use o tipo Sensitive/Encrypted no painel da Vercel.

O backend usa PostgreSQL com o driver psycopg. Prefira a URL pooled fornecida pelo Neon para tráfego da aplicação.

A autenticação usa cookie de sessão `HttpOnly` e cookie CSRF separado. Como os hosts `web-*.vercel.app` e `api-*.vercel.app` podem ser tratados como sites distintos pelo navegador, a configuração de preview exige `Secure=true` e `SameSite=none`. Isso requer HTTPS. A lista CORS deve conter a origem Web exata; nunca use `*` com credenciais. A disponibilidade de cookies de terceiros varia por navegador, portanto o teste real do fluxo no preview continua obrigatório.

## Variáveis da Web

Configure no projeto Vercel `web`:

| Variável | Preview | Produção |
| --- | --- | --- |
| `VITE_API_URL` | URL HTTPS do preview da API | URL HTTPS definitiva da API |

Variáveis com prefixo `VITE_` são incorporadas ao bundle público. Nunca coloque senhas, tokens privados ou strings de conexão nelas.

## Migrações

A API usa Alembic. Antes de liberar um ambiente:
1. Confirme que `DATABASE_URL` aponta para o banco correto.
2. Execute `alembic upgrade head` no diretório `apps/api`.
3. Confirme `alembic current` e verifique as tabelas `users`, `campaigns`, `characters`, `points_of_interest` e `alembic_version`.
4. Faça o teste de cadastro, login, criação de campanha e isolamento entre duas contas.
5. Não copie dados de homologação para produção.

A migração 0004 mantém `campaigns.user_id` anulável para preservar campanhas antigas sem proprietário. Elas não aparecem na lista autenticada e não devem ser atribuídas automaticamente a uma conta.

## Teste mínimo após cada deployment

- `GET /health` retorna HTTP 200.
- Cadastro cria uma conta e define cookies de sessão; a resposta JSON não contém bearer token.
- Login com senha incorreta retorna HTTP 401.
- `GET /api/v1/auth/me` exige cookie de sessão `HttpOnly`.
- Sem cookie de sessão, operações de campanha retornam HTTP 401; mutações com Origin exigem CSRF válido.
- Uma conta não consegue ler ou alterar campanha de outra conta.
- O navegador consegue chamar a API sem erro de CORS.
- Criar campanha, criar personagem, mover, consumir item, descansar e retomar após novo login.

## Situação desta etapa

A Vercel reportou os previews da PR #19 como `Ready`; isso confirma o build, não a configuração de variáveis nem o fluxo de autenticação em navegador. O Neon possui o projeto e banco `amazonia`; a migração equivalente à cadeia Alembic até `0004_user_accounts` foi aplicada e verificada na branch principal em 2026-11-14. Nenhuma conta ou dado pessoal foi inserido. Antes de liberar o preview, confirme as variáveis descritas acima e execute o teste integrado com duas contas.
