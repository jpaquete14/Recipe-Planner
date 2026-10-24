# Instruções para o GitHub Copilot (Recipe-Planner)

Este repositório é um **Guia de Receitas e Planeador de Lista de Compras**.

## 🇵🇹 Idioma Obrigatório
- Todas as respostas, receitas, planos de refeições, listas de compras e mensagens devem ser formuladas em **Português de Portugal (pt-PT)**.
- Utilize terminologia comum em Portugal (ex.: *lacticínios*, *pequeno-almoço*, *refeições*, *almoço*, *jantar*, *frutas e legumes*, *talho*, *azeite*, *especiarias*).

## 📁 Estrutura do Repositório
- `web/`: Interface gráfica de utilizador no navegador (HTML, CSS, JS).
- `app.py`: Servidor Web local (standard library, zero dependências extras).
- `iniciar.bat`: Atalho de arranque com duplo clique para abrir a aplicação e o navegador.
- `recipes/`: Contém ficheiros `.txt` individuais de receitas do dia-a-dia.
- `recipes/_modelo.txt`: Ficheiro de modelo padrão para novas receitas.
- `src/recipe_parser.py`: Leitor e analisador de receitas e ingredientes.
- `src/planner.py`: Motor de planeamento, cálculo de refeições, escala de doses e substituição de pratos.
- `src/shopping_list.py`: Consolidação de ingredientes e geração da lista de compras categorizada.
- `planner.py`: Interface alternativa de linha de comandos (CLI).
- `.plano_atual.json`: Ficheiro de estado que guarda o plano de refeições e escolhas ativas.

## 📝 Formato das Receitas (`recipes/*.txt`)
Ao criar novas receitas a pedido do utilizador, crie um novo ficheiro `.txt` na pasta `recipes/` (ex: `recipes/frango_no_forno.txt`) com a estrutura de `_modelo.txt`:
```text
Título: Nome da Receita
Doses: 4
Tempo de Preparação: 15 min
Tempo de Cozedura: 30 min
Categoria: Almoço, Jantar
Dificuldade: Fácil

Ingredientes:
- 500 g de peito de frango [Talho]
- 1 unidade de cebola média, picada [Frutas e Legumes]
- 2 dentes de alho, picados [Frutas e Legumes]
- 2 c. de sopa de azeite [Azeites e Óleos]
- 1 c. de chá de sal [Especiarias e Temperos]

Instruções:
1. Passo 1...
2. Passo 2...

Notas:
- Dicas ou substituições...
```
Secções recomendadas de supermercado entre parêntesis retos:
`[Frutas e Legumes]`, `[Talho]`, `[Peixaria]`, `[Lacticínios e Ovos]`, `[Padaria]`, `[Mercearia]`, `[Azeites e Óleos]`, `[Especiarias e Temperos]`, `[Congelados]`.

## 🤖 Como Responder aos Pedidos do Utilizador no Chat
1. **Adicionar nova receita**:
   - Crie o ficheiro correspondente em `recipes/<nome_receita>.txt` respeitando o modelo.
2. **Pedir plano de refeições ou lista de compras**:
   - Exemplo: *"Faz-me um plano para 1 semana para 2 pessoas"* -> 1 semana = 14 refeições (7 dias x 2 refeições/dia).
   - Exemplo: *"Cria uma lista para 2 dias só com 1 refeição"* -> 2 dias = 4 refeições; a refeição selecionada cobrirá as 4 refeições (as doses aumentam proporcionalmente para o número de pessoas).
   - Exemplo: *"Quero 2 refeições diferentes para 7 dias e 1 pessoa"* -> 14 refeições divididas por 2 receitas distintas (7 refeições/doses cada).
   - Pode executar diretamente o comando CLI através do PowerShell:
     `python planner.py planear --dias D --pessoas P [--refeicoes-diferentes N] [--escolher "receita:N"] --lista-compras`
     ou apresentar a resposta formatada com o plano e a lista de compras categorizada por secções.
3. **Substituir / trocar refeições**:
   - Exemplo: *"Troca o caril por salmão"* ->
     Execute `python planner.py trocar --remover "caril" --adicionar "salmao" --lista-compras`
     ou atualize o estado e apresente a nova lista de compras.
