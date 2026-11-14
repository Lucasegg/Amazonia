# Amazonia — Blueprint Técnico do Protótipo (Fase 1)

**Status:** proposta técnica para orientar a primeira implementação; escolhas de fornecedor e detalhes de infraestrutura ainda dependem de validação.  
**Base de design:** `docs/GAME_DESIGN_PHASE_0.md` e `docs/PHASE_0_RULES_AND_STORY_DRAFT.md`.  
**Objetivo:** construir um protótipo pequeno, testável e expansível, sem antecipar sistemas de mundo aberto continental ou multiplayer.

## 1. Objetivo da Fase 1

Entregar uma experiência vertical jogável na Grande São Paulo em que uma pessoa consiga:

1. iniciar uma campanha e criar um personagem com uma das três origens aprovadas;
2. visualizar sua posição em um mapa 2D;
3. explorar locais próximos e descobrir pontos de interesse;
4. executar ações que consomem tempo e podem exigir testes;
5. administrar inventário, fome, sede, fadiga, saúde e ferimentos;
6. encontrar uma ameaça zumbi básica e decidir evitar, investigar ou enfrentar;
7. encontrar pistas e registrar descobertas;
8. salvar e retomar a campanha com o estado consistente.

**Critério central:** uma sessão curta deve demonstrar o ciclo explorar → decidir → executar → sofrer consequência → atualizar o mundo → salvar.

## 2. Limites explícitos do protótipo

### Dentro do escopo
- Um jogador e uma campanha por vez no primeiro fluxo.
- Uma área delimitada da Grande São Paulo.
- Mapa 2D e narrativa textual.
- Três origens: bombeiro, profissional de saúde e mecânico.
- Atributos, testes e progressão de habilidades conforme o documento de regras aprovado.
- Inventário simples, recursos básicos e condições de sobrevivência.
- Um comportamento básico de zumbi baseado em estímulos.
- Pontos de interesse e pistas pré-configurados.
- Persistência e retomada de campanha.
- Mestre de IA limitado a narrar e sugerir ações com base nos resultados do motor de regras.

### Fora do escopo
- Multiplayer, chat entre jogadores ou mundo compartilhado.
- Mapa de toda a América do Sul em alta resolução.
- Simulação ecológica complexa, mutações avançadas e comportamento animal sofisticado.
- Economia completa, construção livre de bases ou crafting extensivo.
- Combate tático complexo, árvore de habilidades extensa e morte permanente definitiva.
- Voz, geração de imagens em tempo real ou cenas 3D.
- Integração com dados pessoais ou localização real do jogador.

Esses itens podem ser avaliados em fases futuras, sem comprometer a arquitetura básica.

## 3. Arquitetura lógica

A arquitetura deve separar interface, regras determinísticas, persistência, dados geográficos e narração.

```text
[Web App: mapa + painel + narrativa]
                 |
              [API]
                 |
       [Orquestrador de ações]
          /      |       \
         /       |        \
 [Motor de   [Serviço de  [Serviço de
   regras]    campanha]    geografia]
      |           |             |
      +-----------+-------------+
                  |
             [PostgreSQL]
                  |
       [Adaptador de IA narradora]
                  |
       [Provedor de modelo externo]
```

### Responsabilidades

**Web App**
- Renderizar mapa, estado do personagem, inventário, diário e narrativa.
- Enviar intenção de ação; não calcular resultados oficiais.
- Exibir custos, riscos conhecidos e resultados retornados pela API.

**API e orquestrador**
- Validar identidade da campanha e estado atual.
- Verificar se a ação é permitida.
- Coordenar motor de regras, atualização do mundo e gravação.
- Garantir que uma ação seja aplicada uma única vez.

**Motor de regras**
- Executar dados, dificuldades, modificadores e consequências.
- Controlar tempo, necessidades, inventário, ferimentos, habilidades e ameaças.
- Ser determinístico quando receber a mesma semente, estado e comando.
- Não depender de chamadas a modelos de IA para decisões numéricas.

**Serviço de campanha**
- Criar, carregar, salvar e encerrar campanhas.
- Registrar eventos e snapshots de estado.
- Manter a sequência cronológica dos acontecimentos.

**Serviço geográfico**
- Resolver células, distâncias, terreno, locais e visibilidade.
- Distinguir informação existente no mundo de informação descoberta pelo personagem.
- Isolar a fonte de dados geográficos do restante das regras.

**Adaptador de IA**
- Receber contexto limitado e estruturado.
- Produzir texto narrativo e opções de ação dentro do contexto fornecido.
- Não escrever diretamente no banco nem alterar atributos, inventário, tempo ou fatos canônicos.

## 4. Fluxo de uma ação

1. O cliente envia `campaign_id`, identificador idempotente, ação pretendida e parâmetros.
2. A API carrega a versão atual da campanha.
3. O orquestrador valida pré-condições, alcance, recursos e permissões.
4. O motor calcula teste, custo de tempo e consequências.
5. O serviço de mundo atualiza apenas entidades afetadas.
6. A transação grava evento, novo estado e versão da campanha.
7. Após a confirmação da gravação, o adaptador de IA recebe o resultado autorizado e o contexto narrativo permitido.
8. A interface apresenta a narração e o novo estado.

Se a narração falhar, a ação e seu resultado mecânico permanecem registrados. A interface pode apresentar uma descrição neutra de contingência e permitir regenerar apenas o texto, sem repetir a ação.

### Consistência e idempotência
- Cada comando de ação recebe uma chave idempotente única.
- A mesma chave não pode consumir recursos ou avançar o tempo duas vezes.
- A gravação do evento e da alteração de estado deve ocorrer na mesma transação.
- A versão da campanha deve ser verificada para impedir que duas ações concorrentes sobrescrevam o mesmo estado.
- O histórico de eventos permite auditoria e reconstrução controlada.

## 5. Modelo de dados inicial

Modelo conceitual; nomes e tipos finais serão definidos na implementação.

| Entidade | Responsabilidade |
|---|---|
| campaigns | campanha, configuração, estado e versão |
| characters | atributos, origem e condições atuais |
| skills | catálogo de habilidades |
| character_skills | nível e pontos de prática por personagem |
| inventory_items | itens, quantidades, condição e localização |
| world_cells | células geográficas e características |
| points_of_interest | locais, estado e conteúdo associado |
| discovered_locations | locais conhecidos por campanha/personagem |
| threats | ameaças, posição, estado e estímulos percebidos |
| canonical_facts | fatos canônicos e dependências narrativas |
| clues | pistas, evidências e condições de descoberta |
| discoveries | conhecimento efetivamente obtido pelo jogador |
| world_events | histórico cronológico e imutável de ações/eventos |
| action_receipts | chaves idempotentes e resultados de comandos |

### Regras de persistência
- Identificadores estáveis para campanha, personagem, local, fato, pista e evento.
- Datas armazenadas em UTC; a apresentação usa o fuso definido para o mundo da campanha.
- Estado atual pode ser materializado para leitura rápida, mas eventos são a trilha de auditoria.
- Exclusões de dados de jogo devem ser tratadas como operações explícitas; não apagar fatos históricos silenciosamente.
- Dados geográficos de terceiros devem guardar origem, licença e atribuição quando aplicável.

## 6. Contratos iniciais da API

Rotas ilustrativas, não contratos finais:

| Método e rota | Finalidade |
|---|---|
| POST /campaigns | criar campanha |
| GET /campaigns/{id} | carregar estado resumido |
| POST /campaigns/{id}/character | criar personagem |
| GET /campaigns/{id}/map | obter área visível e descoberta |
| POST /campaigns/{id}/actions | executar ação idempotente |
| GET /campaigns/{id}/events | consultar diário/histórico |
| GET /campaigns/{id}/inventory | consultar inventário |
| POST /campaigns/{id}/save | criar snapshot explícito, se necessário |

A API deve validar todos os parâmetros no servidor. O cliente nunca deve enviar como verdade um resultado de dado, quantidade de item, valor de atributo ou estado de ameaça.

## 7. Geografia e mapa

### Estratégia
- Começar com um recorte geográfico pequeno e documentado da Grande São Paulo.
- Usar células/hexágonos como unidade de abstração para deslocamento e simulação ampla.
- Manter pontos de interesse com coordenadas e metadados próprios.
- Aumentar o detalhe apenas em áreas jogáveis e locais relevantes.
- Separar coordenadas reais, geometria de exibição e regras de navegação.

### Fontes e licenças
OpenStreetMap pode ser avaliado como fonte de dados cartográficos, observando atribuição e termos aplicáveis. A escolha de provedor de tiles deve considerar política de uso, limites, disponibilidade e custos; não presumir que servidores públicos de tiles sejam hospedagem gratuita para produção.

MapBiomas, IBGE e outras fontes públicas podem ser avaliadas para biomas, limites e contexto territorial em etapas posteriores. Para o protótipo urbano, não importar conjuntos de dados enormes sem necessidade.

### Privacidade
A localização do personagem é fictícia e pertence ao mundo do jogo. Não solicitar nem usar localização GPS do jogador no protótipo.

## 8. Mestre de IA: limites e contrato

A IA é um componente de apresentação narrativa, não o motor do jogo.

### Entrada permitida
- descrição da cena;
- estado resumido e autorizado do personagem;
- ação escolhida;
- resultado mecânico calculado;
- fatos canônicos relevantes;
- pistas já descobertas e informações que o personagem pode perceber;
- estilo e limites de tamanho da resposta.

### Saída esperada
Estrutura validável contendo:
- texto narrativo;
- descrição sensorial compatível com os fatos;
- consequências já calculadas, sem alterá-las;
- opções de próxima ação que sejam apenas sugestões e passem por validação do servidor.

### Restrições obrigatórias
- Não inventar itens, personagens, locais, pistas, fatos ou resultados mecânicos.
- Não revelar fatos canônicos ainda desconhecidos.
- Não transformar hipótese de personagem em verdade.
- Não avançar relógio, consumir recurso ou mover entidade.
- Não executar comandos diretamente no banco.
- Se o contexto for insuficiente, narrar apenas o que é conhecido ou solicitar esclarecimento ao orquestrador.
- Validar saída estruturada; se inválida, usar resposta de contingência.

### Independência do provedor
Criar uma interface/adaptador para trocar o modelo sem alterar regras ou domínio. Registrar versão do modelo, parâmetros não secretos, latência, custo estimado e falhas, sem armazenar segredos em logs.

## 9. Segurança e integridade

- Segredos apenas em variáveis de ambiente ou gerenciador de segredos; nunca no repositório.
- Validar entrada e limitar tamanho/frequência das requisições.
- Aplicar autorização por campanha em toda consulta e mutação.
- Não confiar em identificadores fornecidos pelo cliente sem validar pertencimento.
- Proteger logs contra conteúdo sensível e prompt injection vindo de pistas/documentos do mundo.
- Tratar textos de fontes externas como dados não confiáveis, nunca como instruções para a IA.
- Separar prompts de sistema, dados do mundo e conteúdo encontrado pelo jogador.
- Implementar limites de custo e fallback para indisponibilidade do provedor de IA.
- Para eventual lançamento público, revisar autenticação, privacidade, moderação, backups e proteção contra abuso antes de abrir cadastro.

## 10. Testes obrigatórios

### Unidade
- fórmula de testes, modificadores e dificuldades;
- progressão e limite anti-repetição;
- consumo de tempo, fome, sede e fadiga;
- inventário, carga e itens;
- ferimentos e tratamentos;
- detecção e perseguição de zumbis;
- condições de descoberta de pistas.

### Integração
- criar campanha e personagem;
- executar ação e persistir consequências;
- repetir a mesma chave idempotente;
- falha do serviço de IA após ação persistida;
- carregar campanha após reinício;
- impedir acesso cruzado entre campanhas;
- verificar transação e versão concorrente.

### Aceitação
- começar campanha com cada uma das três origens;
- explorar e descobrir local;
- executar uma ação com sucesso e uma com falha;
- observar custo de tempo e necessidades;
- encontrar ameaça e escapar sem combate;
- encontrar uma pista sem revelar automaticamente sua interpretação verdadeira;
- salvar, sair e retomar sem perda ou duplicação.

## 11. Observabilidade e operação

Registrar, sem dados secretos:
- identificador da campanha e do evento;
- tipo de ação e duração do processamento;
- versão do estado antes/depois;
- resultado do motor de regras;
- falhas de persistência e idempotência;
- latência e falhas do adaptador de IA;
- estimativa de tokens/custo por narração.

O sistema deve funcionar em modo degradado sem IA para ações mecânicas e persistência. Uma indisponibilidade do narrador não pode corromper ou bloquear a campanha.

## 12. Plano incremental de implementação

**Sprint 1 — Fundação**
- estrutura do projeto, ambiente local, banco e migrações;
- modelo de campanha/personagem;
- testes automatizados do motor de regras;
- sem integração de IA ainda.

**Sprint 2 — Ciclo de jogo**
- mapa 2D com recorte inicial;
- movimento e descoberta de locais;
- inventário e condições de sobrevivência;
- persistência de eventos e retomada.

**Sprint 3 — Ameaças e narrativa**
- zumbi básico e estímulos;
- pistas e banco de verdades;
- adaptador de IA com contexto restrito;
- fallback sem IA.

**Sprint 4 — Vertical slice**
- fluxo completo de início a salvamento;
- interface integrada;
- testes de aceitação e correções;
- avaliação de desempenho e custos.

O escopo de cada sprint será refinado em PRs pequenos e revisáveis. Nenhum PR deve introduzir serviços pagos ou recursos fora do limite gratuito sem avaliação e aprovação.

## 13. Decisões técnicas ainda necessárias

Antes de iniciar Sprint 1, escolher e registrar:
1. framework web e biblioteca de mapa;
2. framework Python para API;
3. banco PostgreSQL e opção de hospedagem para desenvolvimento;
4. provedor de tiles/dados geográficos para o recorte;
5. provedor de IA e orçamento/limite de uso;
6. ambiente de deploy e estratégia de segredos;
7. se o primeiro protótipo será executado localmente ou publicado em ambiente privado.

A seleção deve comparar custo real, limites gratuitos, facilidade de migração, exportação de dados, licença e dependência de fornecedor. Não assumir que plano gratuito é ilimitado ou permanente.

## 14. Definição de pronto do blueprint

Este blueprint estará pronto para orientar código quando:
- os limites do protótipo estiverem aceitos;
- as fronteiras entre motor determinístico e IA estiverem preservadas;
- o fluxo de ação e persistência estiver definido;
- o modelo conceitual cobrir campanha, personagem, mundo, eventos e descobertas;
- os testes mínimos estiverem definidos;
- as escolhas de framework e hospedagem forem aprovadas.

---
**Nota:** este documento é uma proposta técnica derivada das decisões de design já aprovadas. Ele não afirma que provedores, bibliotecas ou limites gratuitos foram verificados ou escolhidos.