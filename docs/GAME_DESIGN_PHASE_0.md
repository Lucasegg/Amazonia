# Amazonia — Documento de Design (Fase 0)

**Status:** rascunho inicial para validação  
**Escopo deste documento:** consolidar os fundamentos do jogo e separar decisões confirmadas de propostas que ainda precisam de aprovação.

## 1. Visão do projeto

Amazonia é um RPG virtual de sobrevivência e narrativa ambientado no Brasil e, em fases futuras, na América do Sul durante um apocalipse zumbi. O mundo deve se apoiar em geografia e dados reais, com regiões e biomas que influenciam deslocamento, recursos, clima e perigos.

O jogo combina:
- exploração de locais reais e ambientes gerados a partir de dados geográficos;
- sobrevivência e gestão de recursos;
- personagens com diferentes experiências de vida;
- habilidades que evoluem principalmente pelo uso e pela prática;
- narrativa em camadas, com revelações graduais;
- mundo persistente que muda com a passagem do tempo.

## 2. Princípios de design

1. **Coerência do mundo:** geografia, distâncias, recursos e consequências devem respeitar as regras estabelecidas.
2. **Progressão por vivência:** personagens melhoram ao praticar; livros e treinamento ajudam, mas não substituem experiência.
3. **Profissões não são classes fixas:** a profissão representa experiência e vantagens iniciais, não limita o que o personagem pode aprender.
4. **Consequências importam:** decisões, ferimentos, consumo de recursos e passagem do tempo afetam o estado do mundo.
5. **Narrativa controlada:** o narrador de IA deve seguir um cânone e um estado de jogo persistidos no sistema, sem inventar fatos que contradigam a história.
6. **Escopo incremental:** validar primeiro um recorte pequeno e divertido antes de expandir para o continente.

## 3. Geografia e escala

### Diretriz inicial

O mapa deve usar geografia real como base, mas não tentar representar cada rua ou edifício de todo o continente. A proposta inicial é:
- células/hexágonos de aproximadamente 5 a 10 km para áreas amplas;
- maior detalhamento em cidades e pontos de interesse relevantes;
- uso futuro de dados do OpenStreetMap para cidades, vias e serviços;
- uso de MapBiomas e IBGE para biomas brasileiros;
- dados abertos de relevo e hidrografia quando necessários.

### Recorte do protótipo

**Proposta:** Grande São Paulo, para validar exploração, deslocamento, pontos de interesse, sobrevivência e encontros antes da expansão.

### Biomas previstos para expansão

- Amazônia
- Cerrado
- Caatinga
- Pantanal
- Mata Atlântica
- Pampa

Cada bioma deverá ter parâmetros próprios de clima, água, alimento, abrigo, deslocamento, visibilidade e riscos. Os valores e regras ainda serão especificados; não devem ser presumidos apenas pelo nome do bioma.

## 4. Personagens e profissões

### Regra central

Profissões são pacotes de experiência inicial. Elas podem conceder conhecimentos, equipamentos iniciais ou pequenos bônus coerentes com a história do personagem, mas não bloqueiam outras trilhas de desenvolvimento.

### Lista candidata para discussão

A lista abaixo é uma proposta de trabalho, não uma seleção definitiva:
1. Bombeiro
2. Profissional de saúde
3. Policial
4. Mecânico
5. Eletricista
6. Agricultor
7. Motorista
8. Cozinheiro
9. Caçador ou mateiro
10. Professor
11. Engenheiro ou técnico de construção
12. Morador em situação de rua — origem/experiência de vida, não profissão formal

A lista final deverá conter entre 10 e 15 opções iniciais, conforme o plano original. Também será necessário definir atributos, conhecimentos iniciais, itens de partida e limites para evitar vantagens desbalanceadas.

## 5. Sistema de habilidades por uso

### Princípio proposto

- Uma habilidade progride quando o personagem a utiliza em uma situação relevante.
- A dificuldade e o contexto da atividade devem influenciar o progresso.
- Tentativas com erro podem gerar aprendizado, mas não devem conceder progresso ilimitado por repetição trivial.
- Livros, instrução e treinamento podem conceder conhecimento ou um bônus inicial pequeno.
- A evolução deve refletir prática, não apenas tempo de jogo ou pontos distribuídos.

### Famílias de habilidades — rascunho

- Sobrevivência: obtenção de água, obtenção de alimento, abrigo e orientação.
- Físicas: resistência, força, agilidade e furtividade.
- Técnicas: mecânica, elétrica, construção e primeiros socorros.
- Operacionais: direção, rastreamento, manejo de ferramentas e armas.
- Sociais: negociação, liderança, percepção e cooperação.

A lista, os níveis, a fórmula de progresso, os testes e os efeitos de falha permanecem pendentes de balanceamento.

## 6. Sobrevivência e ameaças

O protótipo deverá contemplar pelo menos:
- fome;
- sede;
- ferimentos;
- passagem do tempo;
- zumbis com comportamento inicial simples.

A implementação deverá manter separadas as condições do personagem, os recursos do inventário e o estado global do mundo. Regras de infecção, cura, descanso, doenças, combate e morte ainda precisam de especificação.

## 7. Mundo dinâmico

O tempo do jogo será um gatilho para mudanças persistentes. Entre os sistemas previstos:
- mutação gradual do vírus;
- alteração do comportamento dos animais;
- escassez ou redistribuição de recursos;
- mudança na eficácia de tratamentos ou cura;
- alterações em locais e ameaças conforme eventos e decisões.

Cada mudança deverá ser representada por estado e regras verificáveis no sistema. O narrador não será a fonte de verdade desses dados.

## 8. Narrativa e banco de verdades

A história terá revelações em camadas. Para evitar contradições, será mantido um **banco de verdades** separado da improvisação do narrador.

Estrutura proposta para cada elemento narrativo:
- identificador;
- fato canônico (o que realmente aconteceu);
- personagens ou grupos que conhecem o fato;
- pistas que podem revelar o fato;
- condições para disponibilizar cada pista;
- versões falsas, incompletas ou interpretações equivocadas;
- consequências no mundo;
- dependências de outros fatos.

**Importante:** este documento ainda não define o evento de origem do apocalipse, os responsáveis, a cronologia ou as reviravoltas. Esses elementos serão criados e validados como parte do design narrativo, sem serem tratados como fatos antes da aprovação.

A IA poderá narrar cenas e diálogos dentro desse contexto, mas o estado do mundo, os fatos canônicos e as descobertas dos jogadores deverão ser persistidos fora da memória do modelo.

## 9. Arquitetura técnica — direção inicial

A direção sugerida para o protótipo é:
- aplicação web acessível pelo navegador;
- mapa com MapLibre ou Leaflet;
- backend em Python;
- banco de dados para personagens, inventário, mapa explorado, eventos e estado do mundo;
- integração com modelo de IA para narração, sempre condicionada ao banco de verdades e ao estado persistido.

A escolha definitiva de serviços, banco, hospedagem e provedor de IA depende de uma análise de custo, limites gratuitos, privacidade e facilidade de manutenção. O custo por uso de IA precisa ser medido antes de abrir o jogo a mais jogadores.

## 10. Plano por fases

### Fase 0 — Design
- definir regras de habilidade e progressão;
- fechar a lista de 10 a 15 profissões iniciais;
- descrever os biomas e seus impactos;
- estabelecer o banco de verdades e a estrutura da trama;
- decidir formato de jogo, público e modo de sessão.

### Fase 1 — Protótipo jogável
- recorte geográfico da Grande São Paulo;
- três profissões;
- habilidades por uso;
- sobrevivência básica: fome, sede e ferimentos;
- zumbis simples;
- narrador de IA com contexto controlado.

Critério principal: comprovar que o ciclo de exploração, decisão, risco e progressão é divertido antes de ampliar o escopo.

### Fase 2 — Expansão
- novos biomas e profissões;
- evolução do vírus e dos animais;
- primeiras pistas da trama;
- maior profundidade de simulação.

### Fase 3 — Escala
- expansão para a América do Sul;
- multiplayer em grupo;
- narrativa completa e sistemas avançados.

## 11. Decisões pendentes do projeto

Estas decisões foram identificadas no estudo de viabilidade e precisam ser confirmadas:
1. **Modo:** jogo individual com mestre de IA ou mesa com amigos jogando juntos?
2. **Apresentação:** narrativa principalmente em texto com mapa ou experiência mais visual com personagens e cenas?
3. **Público:** uso pessoal e amigos ou intenção de lançamento público?

Outras decisões de design, como perspectiva, dificuldade, combate, morte permanente, salvamento e ritmo do tempo, serão detalhadas depois que essas três escolhas estiverem encaminhadas.

## 12. Próxima etapa

Revisar este rascunho, fechar as decisões pendentes e então detalhar:
- ficha do personagem e atributos;
- catálogo definitivo de habilidades;
- regras de ganho de experiência por uso;
- pacotes iniciais das três profissões do protótipo;
- regras de fome, sede, ferimentos e ameaças;
- cronologia canônica e banco de verdades da trama.

---
**Referência de origem:** documento de viabilidade e plano do projeto “RPG de Apocalipse Zumbi na América do Sul”. Este arquivo transforma as diretrizes iniciais em uma base de design; itens marcados como proposta ou pendentes não são decisões finais.
