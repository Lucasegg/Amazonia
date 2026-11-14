# Deploy Amazonia na Vercel e conectar ao Neon

Este repositório é um monorepo com dois projetos Vercel independentes:
- API: diretório raiz `apps/api`
- Web: diretório raiz `apps/web`

O status `Ready` confirma build/deployment, mas não substitui teste HTTP de ponta a ponta nem confirma variáveis de ambiente.

## Variáveis da API

Configure no projeto Vercel `api`:

| Variável | Preview | Produção |
| --- | --- | --- |
| `DATABASE_URL` | URL pooled do banco Neon de homologação | URL pooled do banco Neon de produção |
| `AMAZONIA_AUTH_SECRET` | Segredo aleatório exclusivo, mínimo 32 caracteres | Outro segredo aleatório exclusivo |
| `AMAZONIA_CORS_ORIGINS` | URL exata do preview Web, sem barra final | Domínio definitivo do Web |
| `AMAZONIA_COOKIE_SECURE` | `true` | `true` |
| `AMAZONIA_COOKIE_SAMESITE` | `none` para hosts Vercel distintos | `none` se os sites forem distintos; `lax` se estiverem sob o mesmo site |

Gere o segredo localmente com `openssl rand -hex 32`. Não reutilize o segredo da CI, não o coloque no Git e não o envie em mensagens. Use o tipo Sensitive/Encrypted no painel da Vercel.

Como Web e API usam hosts Vercel diferentes, o preview exige `Secure=true` e `SameSite=none`, ambos sobre HTTPS. A lista CORS deve conter a origem Web exata; nunca use `*` com credenciais. Restrições de cookies de terceiros variam por navegador.

## Variáveis da Web

| Variável | Preview | Produção |
| --- | --- | --- |
| `VITE_API_URL` | URL HTTPS do preview da API | URL HTTPS definitiva da API |

Variáveis com prefixo `VITE_` são públicas no bundle. Nunca coloque segredos nelas.

## Migrações

A API usa Alembic. Antes de liberar um ambiente:
1. Confirme que `DATABASE_URL` aponta para o banco correto.
2. Execute `alembic upgrade head` em `apps/api`.
3. Confirme `alembic current` e verifique `users`, `campaigns`, `characters`, `points_of_interest`, `auth_attempts` e `alembic_version`.
4. Confirme que a versão é `0005_auth_hardening`.
5. Teste cadastro, login, logout e isolamento entre duas contas.
6. Não copie dados de homologação para produção.

A migração 0004 mantém `campaigns.user_id` anulável para preservar campanhas antigas sem proprietário. A 0005 adiciona `users.session_version` e `auth_attempts`. O logout incrementa a versão e invalida sessões emitidas anteriormente. Limites atuais: 5 falhas por e-mail em 15 minutos, 20 falhas por IP em 15 minutos e 5 cadastros por IP por hora. Identificadores são guardados como HMAC.

## Teste mínimo após cada deployment

- `GET /health` retorna HTTP 200.
- Cadastro cria uma conta e define cookies; JSON não contém bearer token.
- Login com senha incorreta retorna HTTP 401; após o limite, retorna HTTP 429.
- `GET /api/v1/auth/me` exige cookie válido.
- Logout invalida também uma cópia anterior do cookie.
- Sem sessão, operações de campanha retornam HTTP 401.
- Mutação de navegador exige Origin permitido e CSRF válido.
- Uma conta não consegue ler ou alterar campanha de outra.
- Criar campanha, personagem, mover, consumir item, descansar e retomar após novo login.

## Limitações antes da produção

Verificação de e-mail e recuperação de senha ainda exigem integração com provedor transacional e credenciais no ambiente. A Vercel reportar `Ready` confirma somente o deployment. Confirme variáveis sem revelar valores e execute o teste real no navegador. Não libere produção até concluir esses pontos.
