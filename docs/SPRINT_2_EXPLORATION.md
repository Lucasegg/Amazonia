# Sprint 2 — Exploração, descoberta e deslocamento

## Escopo

Esta etapa transforma o mapa de referência em um primeiro loop jogável. O personagem recebe um ponto inicial fictício no Centro de São Paulo, pode procurar locais próximos e caminhar até locais já descobertos. O servidor é a autoridade para localização, tempo e histórico.

## Dados geográficos

As coordenadas dos pontos iniciais foram transcritas de bases públicas da Prefeitura de São Paulo:
- Anexo I da Portaria SIURB nº 1/2019, lista de localidades e coordenadas: https://legislacao.prefeitura.sp.gov.br/portaria-secretaria-municipal-de-infraestrutura-e-obras-siurb-1-de-11-de-janeiro-de-2019/anexo/5e14b3a91411926000a591fb/Anexo%20I%20da%20Portaria%20SIURB%20n%C2%BA%201_2019.pdf
- Relação municipal de 240 pontos, com coordenadas: https://drive.prefeitura.sp.gov.br/cidade/secretarias/upload/240%20pontos%20edital.pdf

O spawn na Praça da Sé é uma escolha provisória para teste, não um local canônico da narrativa. Não há GPS, endereço pessoal ou localização real do jogador envolvida.

## Regras provisórias de exploração

- O personagem começa conhecendo somente a Praça da Sé.
- A busca revela o ponto de interesse desconhecido mais próximo, desde que esteja a até 2 km.
- Cada busca avança 15 minutos no relógio da campanha.
- O deslocamento só pode ter como destino um local já descoberto.
- A velocidade de caminhada usada para estimar tempo é 4 km/h; o tempo é arredondado para cima em minutos.
- Essas constantes são parâmetros iniciais de balanceamento e poderão mudar após testes de jogo.
- Necessidades de fome, sede, fadiga e saúde ainda não mudam nesta entrega; os ritmos de consumo serão definidos separadamente.

## Integridade e persistência

- Posição e locais descobertos ficam persistidos na ficha.
- Cada ação gera um evento imutável na campanha.
- Chave de idempotência por campanha impede que repetição de uma mesma requisição aplique a ação duas vezes.
- O mapa retorna somente locais descobertos; pontos desconhecidos não são enviados ao navegador.
- Distância, descoberta, destino permitido e tempo são calculados no servidor.

## Fora do escopo

IA narradora, combate, zumbis, inventário dinâmico, rotas por ruas, trânsito, fome/sede/fadiga automáticas, multiplayer e mapa offline.
