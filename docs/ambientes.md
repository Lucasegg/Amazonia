# Ambientes e infraestrutura do Amazonia

## Estado real da infraestrutura

O projeto Neon atualmente provisionado para o Amazonia é:
- Projeto: `amazonia`
- Região: `aws-sa-east-1` (São Paulo)
- Banco PostgreSQL: `amazonia`
- Branch padrão: `main`
- Migrações aplicadas e verificadas: `0001` até `0007`

**Importante:** no momento existe uma única branch padrão no projeto Neon. Branches temporárias foram criadas exclusivamente para validar migrações e não devem ser tratadas como ambientes permanentes de homologação ou produção. A separação física de bancos/ambientes ainda precisa ser planejada antes de abrir o jogo ao público.

## Vercel

O repositório é um monorepo:
- API: `apps/api`
- Web: `apps/web`

A Vercel já reportou previews Ready em PRs anteriores, mas os deployments mais recentes foram bloqueados pelo limite diário do plano Hobby (mais de 100 deployments em 24 horas). A listagem atual de projetos disponível pela integração não confirmou os projetos API/Web nem permitiu verificar suas variáveis. Portanto, não considerar o deploy atual validado até recuperar o acesso, confirmar os projetos e executar o teste ponta a ponta.

## Configuração obrigatória da API

Configure no ambiente da API, usando o gerenciador de segredos da plataforma:
- `DATABASE_URL`: conexão pooled do Neon para o ambiente correto.
- `AMAZONIA_AUTH_SECRET`: segredo aleatório exclusivo, mínimo 32 caracteres.
- `AMAZONIA_CORS_ORIGINS`: origem HTTPS exata do frontend, sem barra final.
- `AMAZONIA_COOKIE_SECURE=true`.
- `AMAZONIA_COOKIE_SAMESITE=none` quando Web e API estiverem em sites diferentes; use HTTPS.
- `AMAZONIA_REQUIRE_EMAIL_VERIFICATION=true`.
- `AMAZONIA_WEB_URL`: URL HTTPS do frontend, sem caminho.
- `AMAZONIA_OWNER_EMAIL`: endereço do proprietário, usado somente após verificação de e-mail.
- `AMAZONIA_SMTP_HOST`, `AMAZONIA_SMTP_PORT`, `AMAZONIA_SMTP_USERNAME`, `AMAZONIA_SMTP_PASSWORD`, `AMAZONIA_EMAIL_FROM`.

Não coloque credenciais no Git, no frontend ou em mensagens. Segredos SMTP e de autenticação devem ser variáveis sensíveis.

## Configuração da Web

No projeto frontend, configure:
- `VITE_API_URL`: URL HTTPS da API.

Variáveis `VITE_*` são incluídas no bundle público e nunca devem conter segredos.

## Migrações e validação

A versão atual do schema é `0007_character_appearance`. Antes de aplicar qualquer nova migração:
1. Confirmar o banco e a branch de destino.
2. Criar branch Neon isolada para teste.
3. Executar `alembic upgrade head` e os testes.
4. Validar tabelas, colunas e `alembic_version`.
5. Somente então aplicar no ambiente de destino correto.

Não executar migrações automaticamente na inicialização da API. Não marcar uma migração como aplicada manualmente sem validar que todo o DDL correspondente foi executado.

## Regras de segurança

- Senhas com Argon2id.
- Sessão assinada em cookie HttpOnly, CSRF para mutações e revogação por versão de sessão.
- Tentativas de login/cadastro limitadas no banco; identificadores persistidos como HMAC.
- Verificação de e-mail obrigatória por padrão.
- Recuperação de senha com token de uso único, armazenado como hash e com expiração.
- Papel `owner` atribuído somente após confirmação do endereço configurado em `AMAZONIA_OWNER_EMAIL`; nenhum endereço de proprietário é hardcoded.
- Não desativar verificação de e-mail em Preview/Production.

## Estado de liberação

O código e as migrações foram integrados, mas o teste real de autenticação ainda depende de:
- Configurar e testar SMTP.
- Confirmar variáveis e domínios dos projetos Vercel.
- Recuperar a cota de deployments da Vercel.
- Testar cadastro, confirmação, login, logout, recuperação e isolamento de campanhas no navegador.
