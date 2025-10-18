# Aplicação de Gráfico Sankey para Análise de Frequência de Palavras

Esta aplicação permite carregar um arquivo CSV contendo perguntas e respostas, e gerar um gráfico de Sankey para visualizar a frequência das palavras mais comuns em cada pergunta.

## Funcionalidades

- Upload de arquivos CSV
- Seleção de coluna (pergunta) para análise
- Ajuste do número de palavras mais frequentes a serem exibidas
- Visualização do gráfico de Sankey com a frequência de palavras
- Tabela com a contagem de palavras

## Requisitos

- Python 3.8 ou superior
- Dependências listadas em `requirements.txt`

## Como instalar

1. Clone ou baixe este repositório
2. Instale as dependências:

```
pip install -r requirements.txt
```

3. Execute a aplicação:

```
streamlit run app.py
```

## Como usar

1. Após iniciar a aplicação, faça upload de um arquivo CSV
2. As duas primeiras colunas do arquivo serão ignoradas
3. Selecione a coluna (pergunta) que deseja analisar
4. Ajuste o número de palavras mais frequentes a serem exibidas
5. Clique em "Gerar Gráfico de Sankey"

## Formato do arquivo CSV

O arquivo CSV deve ter pelo menos 3 colunas. As duas primeiras serão ignoradas, e as demais serão consideradas como perguntas para análise.

## Observações

- Palavras muito curtas (menos de 3 letras) são automaticamente filtradas
- Palavras comuns (stop words) como artigos e preposições são removidas da análise
- A análise é realizada apenas no texto das respostas na coluna selecionada