# Requisitos — conta, privacidade e criação de personagem

Este documento registra requisitos de produto e critérios de aceite. Não substitui parecer jurídico, inventário de dados, definição formal de controlador/operadores ou revisão de segurança.

## 1. Identidade e acesso

A experiência deve oferecer duas formas de entrada:
- E-mail e senha, aceitando endereços Gmail e de outros provedores.
- Continuar com Google, por OAuth 2.0 / OpenID Connect.

Regras obrigatórias para Google:
- Validar no servidor assinatura, issuer, audience, expiração, nonce/state e e-mail verificado.
- Usar Authorization Code + PKCE quando aplicável; não confiar em dados de perfil enviados livremente pelo navegador.
- Não vincular automaticamente uma identidade Google a uma conta existente apenas porque os e-mails coincidem. Exigir autenticação na conta existente ou fluxo explícito de vinculação.
- Guardar o identificador estável do provedor (sub), não tokens Google desnecessários.
- Client ID e segredos somente em variáveis protegidas; nunca no Git. O Client ID pode ser público no front-end, mas o segredo não.

Sessões:
- Não persistir bearer token em localStorage/sessionStorage.
- Preferir cookie de sessão HttpOnly, Secure e SameSite adequado ao domínio, com proteção CSRF e CORS restrito às origens reais.
- Implementar expiração, renovação controlada, logout/revogação e rotação de sessão.
- Aplicar limitação de tentativas e proteção contra enumeração/abuso no cadastro, login e recuperação.

Conta por senha:
- Verificação de posse do e-mail antes de habilitar a conta.
- Recuperação de senha com token de uso único, curta validade e resposta que não revele se o e-mail existe.
- Hash Argon2id; nunca armazenar senha em texto puro.
- Mensagens de erro neutras e auditoria sem registrar senha, token ou código de recuperação.

## 2. Privacidade e proteção de dados

A referência legal brasileira é a LGPD (Lei 13.709/2018) e a autoridade reguladora é a ANPD — não “ANPPD”. O projeto deve ser construído com privacidade desde a concepção e por padrão.

Antes de disponibilizar contas ao público:
- Mapear dados coletados, finalidade, hipótese legal, prazo de retenção, compartilhamentos e operadores.
- Publicar Aviso/Política de Privacidade claro, com controlador, contato do encarregado quando aplicável, finalidades, direitos e canais de atendimento.
- Coletar apenas e-mail, nome de exibição e dados técnicos estritamente necessários; não solicitar data de nascimento, telefone, localização GPS ou documentos sem necessidade justificada.
- Separar dados da conta dos dados do jogo; nunca expor e-mail ou identificadores privados em mapas, rankings ou conteúdo público.
- Oferecer fluxo de acesso, correção, exportação e exclusão de dados/conta; explicar retenções legais e backups.
- Definir retenção e descarte para contas inativas, logs, tokens, backups e solicitações de titulares.
- Restringir acesso administrativo por menor privilégio, MFA para acesso operacional e trilha de auditoria sem segredos.
- Criptografar tráfego em trânsito, proteger segredos, restringir conexões do banco, separar homologação/produção e manter backups/restauração testados.
- Criar plano de resposta a incidentes e processo para avaliar comunicação à ANPD e aos titulares nos prazos regulamentares.
- Avaliar contratos e papéis de controlador/operador com hospedagem, banco, e-mail e autenticação; verificar transferências internacionais e salvaguardas aplicáveis.

A aparência de um personagem fictício é dado de jogo, não deve ser usada para inferir ou classificar características reais do jogador. Não pedir fotos, biometria ou dados sensíveis para personalização.

## 3. Editor de personagem

O jogador pode escolher:
- Nome do personagem.
- Cabelo: estilo/corte e cor.
- Olhos: cor.
- Pele: tom em paleta de jogo.
- Tatuagens: nenhuma ou opções de catálogo, com posição e escala permitidas.
- Camiseta: modelo e cor.
- Calça: modelo e cor.
- Profissão/origem inicial: escolher entre profissões liberadas no catálogo do jogo.

Regras:
- Aparência é cosmética e não altera atributos, habilidades ou probabilidades.
- Profissão/origem define apenas o pacote inicial de habilidades, itens e vantagem contextual do catálogo.
- Valores devem ser enums/listas permitidas pelo servidor; nunca aceitar CSS/HTML/URLs arbitrários do usuário.
- Salvar a configuração no personagem e retornar a mesma configuração ao retomar campanha.
- O editor deve mostrar prévia do avatar em camadas (corpo/pele, cabelo, olhos, tatuagem, camiseta e calça). Os recursos visuais devem ser assets originais ou licenciados.
- A interface deve ser acessível por teclado, ter rótulos e não depender apenas de cor.

## 4. Ponto de início e bioma aleatórios

O jogador NÃO escolhe município, coordenada, célula, região ou bioma inicial.

Ao criar personagem/campanha:
1. O servidor escolhe a região/célula usando fonte aleatória criptograficamente segura.
2. O sorteio considera somente células de spawn publicadas no conjunto geográfico do jogo, com coordenadas e bioma validados.
3. O bioma é determinado pela camada geográfica/dataset, não escolhido pelo cliente.
4. A distribuição deve ser ponderada e configurável para evitar concentrações injustas; regras de segurança do jogo podem excluir células inadequadas.
5. O servidor persiste a semente/resultado necessário para auditoria e a posição inicial; repetir requisição não deve sortear um novo início.
6. O cliente recebe a região descoberta pelo personagem, sem campo para enviar ou alterar posição inicial.
7. Testes verificam que o cliente não consegue escolher coordenadas/bioma e que os resultados permanecem dentro das células elegíveis.

Dependência geográfica: o protótipo atual usa centro fixo em São Paulo e uma grade local. Portanto, o sorteio inicial amplo por biomas brasileiros/sul-americanos depende primeiro de importar e validar cobertura geográfica real para as regiões e biomas que serão habilitados. Não fingir variedade global com dados que ainda não existem. Até essa ingestão, o ambiente deve deixar explícito que o conjunto de spawn é limitado ao protótipo.

## 5. Critérios de aceite

- Login/cadastro com Gmail por senha funciona.
- Login/cadastro Google funciona com verificação OIDC no servidor.
- Não há bearer token persistente acessível a JavaScript.
- Duas contas não conseguem acessar campanhas, personagens, mapa ou inventário uma da outra.
- Titular consegue solicitar exportação e exclusão; o processo respeita retenções documentadas.
- Aparência e profissão persistem após logout/login.
- Cliente não consegue enviar localização inicial ou bioma.
- O servidor sorteia um spawn válido e reproduzível para a campanha.
- CI cobre autenticação, abuso, isolamento, privacidade e sorteio.
- Nenhum deploy público antes da revisão de segurança, configuração de segredos e validação jurídica/privacidade.


## 6. Conta proprietária da plataforma

O projeto terá uma função global `owner` para o responsável pelo Amazonia, separada de papéis comuns de jogador e de permissões de campanha.

- A conta proprietária inicial será provisionada por configuração operacional explícita (`AMAZONIA_OWNER_EMAIL`) e somente após verificação de posse do endereço.
- Nunca conceder `owner` apenas porque alguém digitou o e-mail durante o cadastro.
- A promoção inicial deve ser idempotente, auditada e executada por bootstrap controlado; não permitir autoelevação via API pública.
- O owner terá acesso administrativo global aos recursos da plataforma, suporte e gestão de contas, mas toda consulta/alteração deverá respeitar finalidade, menor privilégio operacional e trilha de auditoria.
- Exigir MFA para operações administrativas quando o mecanismo de identidade estiver disponível; não permitir credenciais administrativas compartilhadas.
- Não expor dados privados de jogadores em ferramentas de administração além do necessário para suporte e segurança.
- A conta owner não será usada como personagem ou conta de teste compartilhada; o usuário deverá poder jogar normalmente com sua conta e campanhas privadas.
- A conta deve poder recuperar acesso com segurança e manter registro de sessões/dispositivos e eventos administrativos.
