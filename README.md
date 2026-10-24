# 🍳 Recipe-Planner — Guia de Receitas e Planeador de Lista de Compras

Sistema modular em **Python** (utilizando apenas a biblioteca padrão, sem dependências externas) e integrado com o **GitHub Copilot** para gerir as suas receitas do dia-a-dia em ficheiros de texto, planear refeições para qualquer período (semanal ou diário), ajustar doses consoante o número de pessoas e gerar listas de compras organizadas por secção de supermercado em **Português de Portugal (pt-PT)**.

---

## ✨ Funcionalidades Principais

- **Ficheiros de Receita Individuais (`.txt`)**: Cada receita tem o seu próprio ficheiro simples e legível na pasta `recipes/`.
- **Formato Padronizado**: Modelo base (`recipes/_modelo.txt`) com doses, tempo estimado, ingredientes com medidas e secções de supermercado, instruções e notas.
- **Planeamento Flexível**:
  - Planear para 1 semana (assume 14 refeições: almoço e jantar para 7 dias) ou para qualquer número de dias/refeições.
  - Ajuste de doses para qualquer número de pessoas (predefinição: 2 pessoas).
  - **Número específico de refeições diferentes**: Possibilidade de definir exatamente quantas receitas/pratos diferentes quer no plano (ex: apenas 2 refeições diferentes para 7 dias e 1 pessoa, ideal para *meal prep* / marmitas), distribuindo as doses e refeições uniformemente.
  - Seleção manual de refeições e preenchimento aleatório das restantes para variedade.
  - **Doses ajustadas por dias**: Se escolher apenas 1 refeição para cobrir 2 dias, as doses são automaticamente multiplicadas para garantir porções suficientes.
- **Troca Fácil de Refeições**: Substitua facilmente uma refeição no plano ativo por outra (`trocar`).
- **Lista de Compras Inteligente**:
  - Consolida ingredientes repetidos entre diferentes receitas.
  - Converte unidades compatíveis (ex: gramas para quilogramas, mililitros para litros).
  - Organiza os itens por corredor do supermercado (*Frutas e Legumes, Talho e Aves, Peixaria, Lacticínios e Ovos, Mercearia, Azeites e Molhos, Especiarias, etc.*).
  - Exportação em formato de lista de verificação (*checklist*) Markdown.
- **Integração com o GitHub Copilot**: Peça em linguagem natural no chat para planear a sua semana, adicionar receitas ou trocar pratos.

---

## 🖥️ Como Utilizar a Interface Gráfica (Sem Terminal)

Esta é a forma mais simples e intuitiva de usar o planeador sem tocar no terminal!

### 🖱️ No Windows (1 clique duplo):
1. Dê um **duplo clique no ficheiro `iniciar.bat`**.
2. O servidor arranca e abre automaticamente a aplicação no seu navegador predefinido: **`http://localhost:8000`**.

### 💻 Ou através do comando:
```bash
python app.py
```

### O que pode fazer na Interface Web:
- **🗓️ Separador "Planeador"**:
  - Escolha o número de dias (com botões rápidos para *1 Semana*, *2 Dias*, *3 Dias*, etc.) e pessoas.
  - Selecione o número de **refeições diferentes** (ex.: 2 pratos diferentes para toda a semana ou variado/automático).
  - Clique em **"✨ Gerar Plano Completo"** para baralhar e preencher automaticamente a ementa.
  - Selecione receitas específicas e ajuste quantas refeições cobrem (com multiplicação automática de doses).
  - Troque qualquer refeição com o botão **"🔄 Trocar"** num simples menu visual.
- **🛒 Separador "Lista de Compras"**:
  - Veja todos os ingredientes somados e organizados por corredor (*Frutas e Legumes, Talho, Peixaria, Lacticínios, Mercearia, etc.*).
  - Caixas de verificação (*checkboxes*) para riscar itens à medida que os coloca no carrinho de compras.
  - Botão **"📋 Copiar para Notas / WhatsApp"** para levar a lista no telemóvel.
  - Botão **"💾 Descarregar Markdown"**.
- **📖 Separador "Livro de Receitas"**:
  - Pesquise e filtre por categorias (*Almoço, Jantar, Rápido, Saudável, Peixe, Carne*).
  - Consulte o modo de preparação e ingredientes completos.
  - **✏️ Editar Receitas**: Altere qualquer receita existente (título, doses, tempos, ingredientes ou instruções) com 1 clique no botão "Editar" ou dentro da janela de detalhes.
- **➕ Separador "Nova Receita"**:
  - Adicione novas receitas através de um formulário visual, gravando automaticamente o ficheiro `.txt` padronizado.

---

## 📁 Estrutura do Repositório

```text
Recipe-Planner/
├── recipes/                            # Receitas do dia-a-dia (.txt)
│   ├── _modelo.txt                     # Modelo padrão para novas receitas
│   ├── arroz_de_frango_com_legumes.txt
│   ├── bacalhau_a_bras.txt
│   ├── chili_com_carne.txt
│   ├── esparguete_a_bolonhesa.txt
│   ├── frango_com_caril.txt
│   ├── salada_mediterranica_com_frango.txt
│   ├── salmao_grelhado_com_legumes.txt
│   └── sopa_rica_de_legumes.txt
├── web/                                # Interface Web Gráfica (HTML/CSS/JS)
│   ├── index.html                      # Aplicação visual de página única
│   ├── style.css                       # Estilos modernos e responsivos
│   └── app.js                          # Lógica interativa da interface
├── src/                                # Motor da aplicação em Python
│   ├── recipe_parser.py                # Analisador de ficheiros .txt e ingredientes
│   ├── planner.py                      # Planeador de refeições e cálculo de doses
│   └── shopping_list.py                # Agregador e gerador da lista de compras
├── tests/                              # Testes unitários (unittest)
├── app.py                              # Servidor Web local (standard library)
├── iniciar.bat                         # Atalho de arranque com 1 clique (Windows)
├── planner.py                          # Interface alternativa de linha de comandos (CLI)
├── .github/copilot-instructions.md     # Instruções de contexto para o Copilot
└── README.md                           # Documentação do projeto
```

---

## 🚀 Como Utilizar a Linha de Comandos (CLI) (Opcional)

Não são necessárias quaisquer instalações de pacotes (`pip`). Apenas necessita de Python 3.8+.

### 1. Listar todas as receitas disponíveis
```bash
python planner.py listar
```
Pode filtrar por categoria:
```bash
python planner.py listar --categoria "peixe"
```

### 2. Ver os detalhes de uma receita
```bash
python planner.py ver "bacalhau_a_bras"
```

### 3. Planear para 1 semana para 2 pessoas (14 refeições)
Gera um plano com seleção aleatória das refeições disponíveis e apresenta a lista de compras:
```bash
python planner.py planear --dias 7 --pessoas 2 --lista-compras
```

### 4. Planear com um número específico de refeições diferentes (ex: meal prep)
Planear para 1 semana (14 refeições) para 1 pessoa com apenas 2 receitas diferentes:
```bash
python planner.py planear --dias 7 --pessoas 1 --refeicoes-diferentes 2 --lista-compras
```
*O sistema seleciona 2 pratos distintos, atribuindo 7 refeições (e 7 doses) a cada um e calculando os ingredientes exatos.*

### 5. Planear para 2 dias escolhendo apenas 1 refeição
Se planear 2 dias para 2 pessoas (4 refeições) e escolher apenas Bacalhau à Brás:
```bash
python planner.py planear --dias 2 --pessoas 2 --escolher "bacalhau:4" --sem-aleatorio --lista-compras
```
*O sistema calcula automaticamente 8 doses necessárias e duplica os ingredientes da receita base.*

### 6. Escolher refeições específicas e preencher o resto aleatoriamente
```bash
python planner.py planear --dias 7 --pessoas 2 --escolher "bolonhesa:4" --escolher "caril:2" --lista-compras
```

### 7. Trocar uma refeição no plano ativo
```bash
python planner.py trocar --remover "caril" --adicionar "salmao" --lista-compras
```

### 8. Consultar ou exportar a lista de compras
Apresentar a lista de compras do plano atual guardado:
```bash
python planner.py lista-compras
```
Exportar para um ficheiro Markdown:
```bash
python planner.py lista-compras --exportar lista_semanal.md
```

---

## 📝 Como Adicionar uma Nova Receita

Crie um novo ficheiro `.txt` dentro da pasta `recipes/` (ex: `recipes/bife_com_cogumelos.txt`) seguindo a estrutura de `recipes/_modelo.txt`:

```text
Título: Bife de Vaca com Molho de Cogumelos
Doses: 2
Tempo de Preparação: 10 min
Tempo de Cozedura: 15 min
Categoria: Almoço, Jantar, Rápido
Dificuldade: Fácil

Ingredientes:
- 2 unidades de bifes de vaca (aprox. 300 g) [Talho]
- 200 g de cogumelos frescos laminados [Frutas e Legumes]
- 2 dentes de alho, picados [Frutas e Legumes]
- 200 ml de natas de culinária [Lacticínios e Ovos]
- 1 c. de sopa de azeite [Azeites e Óleos]
- 1 c. de sopa de manteiga [Lacticínios e Ovos]
- 1 c. de chá de sal [Especiarias e Temperos]
- 1 pitada de pimenta preta moída [Especiarias e Temperos]

Instruções:
1. Temperar os bifes com sal e pimenta.
2. Numa frigideira bem quente, derreter a manteiga com o azeite e selar os bifes ao seu gosto. Retirar e reservar.
3. Na mesma frigideira, saltear o alho e os cogumelos até dourarem.
4. Adicionar as natas, baixar o lume e deixar apurar até o molho engrossar ligeiramente.
5. Devolver os bifes à frigideira durante 1 minuto e servir de imediato.

Notas:
- Fica excelente acompanhado com arroz branco ou puré de batata.
```

### Categorias recomendadas para a lista de compras:
- `[Frutas e Legumes]`
- `[Talho]` ou `[Talho e Aves]`
- `[Peixaria]`
- `[Lacticínios e Ovos]`
- `[Padaria]`
- `[Mercearia]`
- `[Azeites e Óleos]`
- `[Especiarias e Temperos]`
- `[Congelados]`

---

## 💬 Utilização com o GitHub Copilot no Chat

Pode simplesmente pedir no chat do Copilot:
- *"Faz um plano de refeições para a próxima semana para 2 pessoas e mostra-me a lista de compras."*
- *"Planeia 3 dias para 2 pessoas. Quero almoçar e jantar Esparguete à Bolonhesa nesses dias."*
- *"Gostava de trocar o caril de frango por bacalhau à brás no plano atual."*
- *"Cria uma nova receita de jardineira de vitela e guarda em recipes/."*

---

## 🧪 Executar Testes Unitários

Para correr a suite de testes automatizados:
```bash
python -m unittest discover -s tests -p "test_*.py"
```
