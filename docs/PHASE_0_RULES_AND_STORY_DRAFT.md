# Amazonia — Regras Fundamentais e Narrativa (Fase 0)

**Status:** proposta de design para validação; não é cânone definitivo.  
**Escopo:** transformar as diretrizes do estudo de viabilidade em um primeiro conjunto coerente de regras para discussão e posterior prototipação.

## 1. Premissas confirmadas do projeto

Estas diretrizes vêm do estudo de viabilidade e das decisões já estabelecidas para o projeto:

- RPG virtual de sobrevivência e narrativa no Brasil e, futuramente, na América do Sul.
- Primeira região jogável: Grande São Paulo.
- Experiência individual, com mestre de IA.
- Mapa 2D acompanhado de narrativa em texto.
- Geografia real como base, com abstração por células/hexágonos de aproximadamente 5 a 10 km em áreas amplas e maior detalhe em locais importantes.
- Profissões representam experiências e vantagens iniciais, não classes que bloqueiam outras habilidades.
- Habilidades evoluem principalmente por uso e prática; erros relevantes também podem ensinar.
- Livros e treinamento concedem ajuda inicial limitada, não substituem a experiência.
- O mundo muda com o tempo: vírus, animais, recursos e eficácia de tratamentos podem evoluir.
- A IA narra dentro de um banco de verdades e do estado persistido do jogo; não é a fonte de verdade do mundo.

## 2. Princípios da experiência

1. **Sobreviver é uma sequência de escolhas:** deslocar-se, descansar, procurar recursos e investigar consomem tempo e podem gerar riscos.
2. **Conhecimento tem contexto:** um personagem pode saber teoria sem ter experiência prática suficiente para executar uma tarefa difícil.
3. **Falhas produzem consequências:** uma tentativa malsucedida pode consumir recursos, gerar ruído, causar ferimento ou alertar ameaças.
4. **Não existe classe fechada:** qualquer personagem pode aprender qualquer habilidade, respeitando tempo, acesso a recursos e prática.
5. **A narrativa não altera regras retroativamente:** o mestre de IA descreve o resultado calculado pelo sistema, sem inventar atributos, itens ou fatos.
6. **O protótipo deve ser mensurável:** regras iniciais precisam ser simples o bastante para testar e ajustar.

## 3. Ficha de personagem — proposta

### 3.1 Atributos

Proposta de cinco atributos, com valores de 1 a 5. O valor 3 representa uma pessoa comum sem especialização extraordinária.

| Atributo | Representa | Exemplos de uso |
|---|---|---|
| Vigor | força física, saúde e resistência | carregar peso, resistir a esforço |
| Coordenação | precisão e controle corporal | manusear ferramentas, equilíbrio |
| Percepção | atenção aos sinais do ambiente | notar ameaças, rastros e detalhes |
| Raciocínio | análise, memória e solução de problemas | reparar, planejar, interpretar pistas |
| Presença | comunicação e influência social | negociar, acalmar, liderar |

**Regra proposta:** modificador do atributo = atributo - 3. Assim, os modificadores variam de -2 a +2.

Os atributos não substituem habilidades. Ter vigor alto, por exemplo, não significa saber lutar ou carregar qualquer peso sem consequências.

### 3.2 Dados da ficha

A ficha também deverá guardar:
- nome, idade e breve histórico;
- profissão/experiência de origem;
- atributos;
- habilidades e progresso individual;
- saúde, fome, sede, fadiga e ferimentos;
- inventário equipado e carga transportada;
- posição no mapa e locais conhecidos;
- condições temporárias, relações e descobertas narrativas.

Idade, histórico e origem são elementos narrativos; não devem gerar bônus automáticos sem regra explícita.

## 4. Testes de ação — proposta inicial

### 4.1 Fórmula

Para uma ação incerta:

**Resultado = 1d20 + modificador do atributo + nível da habilidade + modificadores situacionais**

O resultado é comparado com uma dificuldade definida antes da rolagem.

| Dificuldade | Valor-alvo | Exemplo ilustrativo |
|---|---:|---|
| Simples | 8 | tarefa rotineira sob condições favoráveis |
| Moderada | 12 | tarefa que exige atenção e alguma prática |
| Difícil | 16 | tarefa técnica ou sob pressão |
| Muito difícil | 20 | tarefa complexa, perigosa ou com poucos recursos |
| Extrema | 24 | situação excepcional; sucesso não é garantido |

Os exemplos são referências de balanceamento, não uma autorização para rolar dados em tarefas triviais. Se não houver incerteza ou consequência relevante, a ação pode ser resolvida diretamente.

### 4.2 Interpretação

- Resultado igual ou superior ao alvo: sucesso.
- Resultado abaixo do alvo: falha, com consequência coerente com a situação.
- Diferença de 5 ou mais acima do alvo: sucesso expressivo, se a ação permitir.
- Diferença de 5 ou mais abaixo do alvo: complicação relevante, se houver risco plausível.

Não há falha crítica automática apenas por tirar 1, nem sucesso impossível apenas por tirar 20: esses extremos podem receber tratamento especial em uma rodada futura de balanceamento.

### 4.3 Modificadores situacionais

O sistema poderá considerar:
- iluminação, clima e terreno;
- ferramentas adequadas ou improvisadas;
- tempo disponível;
- fadiga, ferimentos e fome/sede;
- ajuda de outra pessoa;
- pressão de ameaça ou combate.

Para evitar contas excessivas, a proposta é usar modificadores pequenos: -2, -1, 0, +1 ou +2. O sistema deve explicar ao jogador os fatores relevantes antes da ação sempre que isso não revelar informação oculta.

## 5. Habilidades e progressão por uso — proposta

### 5.1 Escala

Cada habilidade possui nível de 0 a 5:

| Nível | Descrição |
|---:|---|
| 0 | sem prática; conhecimento apenas intuitivo ou inexistente |
| 1 | noções básicas |
| 2 | iniciante com prática |
| 3 | competente |
| 4 | especialista experiente |
| 5 | domínio excepcional |

O nível é somado diretamente ao teste. O nível 5 deve ser raro e exigir experiência acumulada em situações variadas.

### 5.2 Famílias iniciais

**Sobrevivência**
- obtenção e purificação de água;
- coleta e preparo de alimentos;
- construção de abrigo;
- orientação e navegação;
- rastreamento.

**Físicas**
- condicionamento;
- escalada e transposição;
- furtividade;
- luta corporal.

**Técnicas**
- primeiros socorros;
- mecânica;
- elétrica;
- construção e reparos;
- conhecimento de plantas e ambiente.

**Operacionais**
- direção;
- uso e manutenção de ferramentas;
- armas de fogo;
- armas improvisadas.

**Sociais e cognitivas**
- negociação;
- liderança;
- investigação;
- leitura de comportamento;
- planejamento.

A lista é um catálogo inicial para discussão. Habilidades muito específicas poderão ser agrupadas no protótipo para evitar uma ficha extensa.

### 5.3 Ganho de prática

Proposta de pontos de prática por evento significativo:

- 1 ponto: uso relevante em situação simples ou tentativa com aprendizado limitado;
- 2 pontos: tarefa moderada, com esforço real ou decisão técnica;
- 3 pontos: tarefa difícil, sob risco ou que exigiu adaptação.

**Limites anti-repetição:**
- repetir uma tarefa trivial sem mudança de contexto não gera novos pontos;
- a mesma atividade repetida em sequência tem retorno reduzido ou nulo;
- uma tentativa precisa envolver decisão, risco, dificuldade ou aprendizado verificável;
- falhar pode gerar prática quando o personagem realmente tentou executar e teve oportunidade de aprender;
- ações automáticas, cliques repetidos e tarefas sem risco não concedem prática.

### 5.4 Custo de evolução

Proposta de pontos necessários para avançar ao próximo nível:

| Avanço | Pontos acumulados exigidos desde o nível anterior |
|---|---:|
| 0 → 1 | 4 |
| 1 → 2 | 8 |
| 2 → 3 | 13 |
| 3 → 4 | 19 |
| 4 → 5 | 26 |

O progresso excedente é carregado para o nível seguinte. Os valores devem ser testados em sessões curtas para evitar evolução rápida demais ou lenta demais.

### 5.5 Aprendizado assistido

- Livro encontrado: pode conceder conhecimento teórico, desbloquear uma tentativa ou reduzir a dificuldade em contexto específico.
- Instrutor: pode acelerar a prática quando existe tempo, segurança e material.
- Treinamento: consome tempo e, quando aplicável, recursos.
- Nenhum livro ou treinamento deve elevar automaticamente várias habilidades ao domínio máximo.

## 6. Profissões e experiências de origem

Profissão é um pacote inicial de contexto, habilidades e equipamentos. Ela não limita o desenvolvimento futuro.

### 6.1 Lista candidata de 12 origens

| Origem | Experiência inicial coerente |
|---|---|
| Bombeiro | resposta a emergências, resgate e segurança |
| Profissional de saúde | primeiros socorros e avaliação de sintomas |
| Policial | procedimentos de segurança e observação |
| Mecânico | diagnóstico e reparo de veículos/equipamentos |
| Eletricista | instalações e riscos elétricos |
| Agricultor | cultivo, solo e produção de alimentos |
| Motorista | condução e conhecimento de rotas |
| Cozinheiro | preparo, conservação e higiene de alimentos |
| Caçador/mateiro | rastreamento e leitura do ambiente |
| Professor | comunicação, organização e ensino |
| Técnico/engenheiro de construção | estruturas, materiais e reparos |
| Pessoa em situação de rua | experiência prática de sobrevivência urbana e leitura de ambientes |

A última opção é uma **experiência de vida/origem**, não uma profissão formal. Sua representação deve ser respeitosa, sem estereótipos ou bônus automáticos baseados em condição social.

### 6.2 Pacotes iniciais do protótipo

Proposta de três origens para cobrir sistemas diferentes:

**Bombeiro**
- habilidades iniciais sugeridas: primeiros socorros 1; construção e reparos 1;
- equipamento inicial sugerido: kit básico de primeiros socorros e ferramenta de resgate simples;
- vantagem contextual: experiência em avaliação de riscos e resposta a emergências.

**Profissional de saúde**
- habilidades iniciais sugeridas: primeiros socorros 2; investigação de sintomas 1;
- equipamento inicial sugerido: kit básico de atendimento;
- vantagem contextual: reconhecer sinais clínicos e organizar atendimento, sem tornar o personagem imune a doenças ou ferimentos.

**Mecânico**
- habilidades iniciais sugeridas: mecânica 2; uso e manutenção de ferramentas 1;
- equipamento inicial sugerido: conjunto compacto de ferramentas;
- vantagem contextual: avaliar defeitos e improvisar reparos compatíveis com peças disponíveis.

Os níveis e itens são provisórios. Os pacotes devem ter valor inicial comparável, sem tornar uma origem claramente superior.

## 7. Sobrevivência — proposta para o protótipo

### 7.1 Relógios de condição

Proposta de escalas de 0 a 100:
- fome: 0 = saciado; 100 = fome crítica;
- sede: 0 = hidratado; 100 = desidratação crítica;
- fadiga: 0 = descansado; 100 = exaustão;
- saúde: 0 = morte ou incapacidade irreversível conforme regra futura; 100 = condição saudável.

Esses valores são indicadores de jogo, não medidas médicas reais. A taxa de mudança depende do tempo, esforço, clima e condições do personagem e precisa ser calibrada.

### 7.2 Ferimentos

Categorias iniciais:
- leve: desconforto e penalidade contextual pequena;
- moderado: limita ações específicas e pode exigir tratamento;
- grave: risco elevado, exige atendimento e pode impedir deslocamento ou combate.

O sistema deve registrar causa, localização, gravidade, tratamento e evolução. Ferimentos não devem desaparecer apenas porque a narrativa avançou.

### 7.3 Tempo e ações

O relógio do mundo avança conforme ações relevantes:
- busca rápida: poucos minutos;
- exploração de edifício: dezenas de minutos;
- deslocamento: calculado por distância, terreno e condição;
- descanso: horas;
- tratamento ou reparo: tempo proporcional à tarefa.

As durações exatas serão definidas no protótipo após testes de ritmo. O mestre de IA não pode avançar o tempo sem registrar o custo da ação.

## 8. Zumbis e ameaças no protótipo

A primeira versão deve usar comportamento simples e legível:
- detectar por visão, audição ou outros estímulos definidos;
- investigar ruídos e movimentação;
- perseguir quando houver detecção suficiente;
- perder o alvo quando houver quebra plausível de contato;
- reagir ao ambiente e a obstáculos de forma consistente.

A dificuldade de um encontro deve considerar quantidade, distância, terreno, visibilidade, ruído, condição do personagem e rotas de fuga. Não se deve gerar ameaça inevitável apenas para forçar combate.

Mutação avançada, classes de zumbis e comportamento animal complexo ficam para a expansão, conforme o plano por fases.

## 9. Estrutura preliminar da trama em camadas

**Atenção:** esta seção é uma proposta de arquitetura narrativa, não o cânone final. Nenhuma organização, pessoa, causa ou evento específico é considerado verdadeiro até aprovação e registro no banco de verdades.

### Camada 1 — Sobrevivência imediata

O personagem começa tentando compreender o colapso local: comunicações interrompidas, serviços indisponíveis, relatos contraditórios e ameaças próximas. O objetivo narrativo é sobreviver e descobrir o que ainda funciona.

### Camada 2 — Cronologia inconsistente

Registros, relatos e evidências locais não coincidem sobre quando e onde os primeiros casos ocorreram. O jogador encontra versões conflitantes e precisa avaliar a confiabilidade das fontes. A existência de contradições é um recurso narrativo; a verdade por trás delas ainda será escrita.

### Camada 3 — Decisões humanas e consequências

As pistas sugerem que decisões humanas, falhas de comunicação, interesses e tentativas de contenção influenciaram a escala da crise. Evitar uma explicação simplista de um único vilão permite múltiplas responsabilidades e perspectivas.

### Camada 4 — Evolução do fenômeno

A pesquisa e a observação indicam que o agente infeccioso e o ambiente não permanecem estáticos. Tratamentos que funcionaram em determinado momento podem perder eficácia, e os padrões de comportamento dos infectados e animais podem mudar. As regras exatas precisam ser definidas no cânone.

### Camada 5 — Verdade e escolha

O jogador reúne evidências suficientes para compreender uma parte substancial do que ocorreu. A revelação não precisa oferecer uma solução perfeita: decisões sobre divulgar informações, proteger pessoas, preservar recursos e testar tratamentos devem ter consequências.

### Regras de distribuição das pistas

- Uma pista não deve aparecer antes de sua condição narrativa ser satisfeita.
- Uma pista pode ser perdida, destruída ou encontrada por caminhos alternativos.
- O jogador pode interpretar uma pista incorretamente; o sistema registra o que foi observado, não presume que a interpretação seja verdade.
- O narrador pode descrever hipóteses de personagens, mas deve distingui-las de fatos canônicos.
- Revelações devem ser sustentadas por mais de uma evidência quando forem centrais para a trama.

## 10. Banco de verdades — modelo de registro

Cada fato canônico deverá ser armazenado como um registro estruturado com:

| Campo | Finalidade |
|---|---|
| ID | identificador estável do fato |
| Fato | descrição objetiva do que realmente ocorreu |
| Data/local | quando e onde ocorreu |
| Conhecedores | personagens ou grupos que sabem do fato |
| Evidências | documentos, objetos, testemunhos ou locais |
| Condições | requisitos para cada pista ficar disponível |
| Interpretações | hipóteses possíveis, corretas ou incorretas |
| Dependências | fatos que precisam ser conhecidos antes |
| Estado do jogador | descoberto, inferido, desconhecido ou contestado |

O narrador recebe apenas os fatos e pistas pertinentes à cena e ao conhecimento atual do personagem. O estado persistente fica no sistema, não apenas no histórico de conversa com a IA.

## 11. Direção da interface e do mapa

Para o primeiro protótipo:
- mapa 2D navegável da região inicial;
- posição atual e áreas já exploradas;
- marcadores de locais relevantes descobertos;
- painel de condição do personagem e inventário;
- área principal de narrativa em texto;
- ações disponíveis apresentadas de forma clara;
- registro de eventos e descobertas.

A interface não deve revelar pontos de interesse, inimigos ou recursos que o personagem ainda não descobriu, salvo informações públicas ou visíveis no mapa.

## 12. Critérios para aprovar esta etapa de design

Antes de iniciar a implementação jogável, precisamos validar:
1. atributos e fórmula dos testes;
2. escala e progressão das habilidades;
3. catálogo e pacotes das três origens iniciais;
4. condições de fome, sede, fadiga, saúde e ferimentos;
5. comportamento básico dos zumbis;
6. estrutura da trama e limites do banco de verdades;
7. ritmo do tempo e das ações;
8. quais informações o mapa revela antes e depois da exploração.

## 13. Testes de mesa recomendados

Executar simulações curtas, sem código, para procurar problemas de balanceamento:

- **Teste A — reparo:** mecânico tenta reparar um veículo com ferramentas adequadas e depois com ferramentas improvisadas.
- **Teste B — atendimento:** profissional de saúde trata ferimento com poucos recursos e sob pressão.
- **Teste C — resgate:** bombeiro atravessa um edifício parcialmente bloqueado para alcançar uma saída.
- **Teste D — progressão:** personagem repete uma tarefa simples e depois enfrenta uma tarefa nova, verificando o limite anti-repetição.
- **Teste E — sobrevivência:** personagem decide entre procurar água, descansar e explorar antes do anoitecer.
- **Teste F — pista narrativa:** o jogador encontra um documento incompleto e formula uma hipótese; o narrador não deve confirmar como verdade algo que o documento não prova.

## 14. Itens que permanecem em aberto

- nome, origem, transmissão e regras exatas do agente infeccioso;
- cronologia canônica e responsáveis por eventos específicos;
- regras de combate detalhadas, morte e recuperação;
- duração exata de cada ação e consumo de necessidades;
- fórmula final de evolução e balanceamento;
- se o projeto será apenas pessoal ou terá lançamento público;
- provedor de IA, hospedagem e banco de dados definitivos, após análise de custo e limites gratuitos.

## 15. Relação com o estudo de viabilidade

Este documento detalha o próximo passo indicado no estudo de viabilidade: regras de habilidade por vivência e rascunho da trama em camadas, mantendo o desenvolvimento em fases. O mapa continental, multiplayer e simulação avançada continuam fora do escopo do primeiro protótipo.

**Fonte-base:** “RPG de Apocalipse Zumbi na América do Sul: Viabilidade e Plano”, documento de viabilidade do projeto. As regras numéricas, os pacotes iniciais e a arquitetura das camadas narrativas acima são propostas novas para validação, não afirmações extraídas literalmente da fonte.
