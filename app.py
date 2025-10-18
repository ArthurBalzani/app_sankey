import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.colors as pc
import plotly.express as px
import re
import csv
from collections import Counter
import nltk
from nltk.corpus import stopwords
import matplotlib.colors as mcolors  # Para conversão de cores

# Configuração da página
st.set_page_config(page_title="Análise de Frequência de Palavras", layout="wide")

# Título
st.title("Gerador de Gráfico Sankey para Frequência de Palavras")

# Função para extrair palavras significativas do texto
@st.cache_data
def extrair_palavras(texto):
    if pd.isna(texto):
        return []
    
    try:
        # Garantir que temos as stopwords
        nltk.download('stopwords', quiet=True)
        stop_words = set(stopwords.words('portuguese'))
        
        # Adicionar stopwords adicionais comuns em português
        stop_words_adicionais = {'pra', 'pro', 'sobre', 'assim', 'então', 'porque', 
                               'muito', 'muita', 'muitos', 'muitas', 'bem', 'mal',
                               'sim', 'não', 'pelo', 'pela', 'pelos', 'pelas'}
        stop_words.update(stop_words_adicionais)
    except:
        stop_words = set()  # Caso falhe, usamos um conjunto vazio
    
    # Garantir que texto é string
    texto_str = str(texto).lower()
    
    # Normalização - remover acentos
    import unicodedata
    texto_norm = unicodedata.normalize('NFKD', texto_str)
    texto_norm = ''.join([c for c in texto_norm if not unicodedata.combining(c)])
    
    # Remover pontuação e converter para minúsculas
    palavras = re.findall(r'\b\w+\b', texto_norm)
    
    # Filtrar stopwords e palavras com menos de 3 caracteres
    palavras = [p for p in palavras if p not in stop_words and len(p) > 2]
    return palavras

# Função para criar gráfico Sankey
def criar_grafico_sankey(textos, n_palavras=20, colorscale=None, cor_no_principal="#1f77b4", 
                         opacidade=0.8, altura=600):
    todas_palavras = []
    for texto in textos:
        todas_palavras.extend(extrair_palavras(texto))
    
    # Contar frequência
    contador = Counter(todas_palavras)
    
    # Se não houver palavras, retornar None
    if not contador:
        return None
    
    # Pegar as N palavras mais comuns
    palavras_comuns = dict(contador.most_common(n_palavras))
    
    # Preparar dados para o Sankey
    nodes_labels = ["Pergunta"]  # Nó de origem
    nodes_labels.extend(palavras_comuns.keys())  # Nós de destino (palavras)
    
    source = []
    target = []
    value = []
    
    # Conexões entre "Pergunta" e palavras
    origem_idx = 0  # Índice do nó "Pergunta"
    for i, (palavra, freq) in enumerate(palavras_comuns.items(), 1):
        source.append(origem_idx)
        target.append(i)
        value.append(freq)
    
    # Definir cores diferentes para cada ligação
    import plotly.colors as pc
    
    # Usar a paleta de cores fornecida ou Viridis como padrão
    if colorscale is None:
        colorscale = pc.sequential.Viridis
    
    # Lista para armazenar cores para cada conexão
    colors = []
    node_colors = []
    
    # Criar uma lista de valores de frequência para normalizar as cores
    freq_values = list(palavras_comuns.values())
    max_freq = max(freq_values) if freq_values else 1
    
    # Converter cor_no_principal de hex para rgba se necessário
    if cor_no_principal.startswith("#"):
        from matplotlib.colors import to_rgba
        rgba = to_rgba(cor_no_principal)
        cor_no_principal = f"rgba({int(rgba[0]*255)}, {int(rgba[1]*255)}, {int(rgba[2]*255)}, {opacidade})"
    
    # Gerar cores para cada conexão baseadas na frequência relativa
    for i, (palavra, freq) in enumerate(palavras_comuns.items()):
        # Normalizar a frequência para obter um valor entre 0 e 1
        normalized_freq = freq / max_freq
        # Obter cor da escala de cores
        color_base = pc.sample_colorscale(colorscale, normalized_freq)[0]
        
        # Se a cor for em formato hex, converter para rgba para aplicar opacidade
        if color_base.startswith("#"):
            from matplotlib.colors import to_rgba
            rgba = to_rgba(color_base)
            color = f"rgba({int(rgba[0]*255)}, {int(rgba[1]*255)}, {int(rgba[2]*255)}, {opacidade})"
        elif color_base.startswith("rgb("):
            # Converter de rgb para rgba
            color_base = color_base.replace("rgb(", "").replace(")", "")
            r, g, b = map(int, color_base.split(","))
            color = f"rgba({r}, {g}, {b}, {opacidade})"
        else:
            # Já é rgba, apenas ajustar opacidade
            color = color_base
        
        colors.append(color)
        node_colors.append(color)
    
    # Criar o gráfico Sankey com cores personalizadas
    fig = go.Figure(data=[go.Sankey(
        node = dict(
            pad = 15,
            thickness = 20,
            line = dict(color = "black", width = 0.5),
            label = nodes_labels,
            # Colorir os nós com cores correspondentes
            color = [cor_no_principal] + node_colors
        ),
        link = dict(
            source = source,
            target = target,
            value = value,
            color = colors  # Cada ligação com sua cor específica
        )
    )])
    
    fig.update_layout(
        title_text="Frequência de palavras na pergunta selecionada",
        font_size=12,
        height=altura,  # Altura personalizável
        # Melhorando o layout geral
        margin=dict(l=25, r=25, t=50, b=25),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
    
    return fig

# Upload do arquivo CSV
uploaded_file = st.file_uploader("Faça upload do arquivo CSV", type=['csv'])

if uploaded_file is not None:
    # Carregar dados
    try:
        # Tentar diferentes opções de parsing para lidar com CSVs problemáticos
        st.info("Tentando processar o arquivo...")
        
        # Opções para o usuário
        with st.expander("Opções avançadas de importação"):
            delimiter = st.text_input("Delimitador", value=";")  # Ponto e vírgula como padrão
            encoding = st.selectbox("Encoding", ["utf-8", "latin1", "ISO-8859-1", "cp1252"], index=0)
            error_bad_lines = st.checkbox("Ignorar linhas problemáticas", value=True)
            
        # Tentar carregar o arquivo com as opções especificadas
        if error_bad_lines:
            df = pd.read_csv(
                uploaded_file, 
                sep=delimiter,
                quotechar=None,  # Sem caractere de citação
                encoding=encoding,
                on_bad_lines='skip',  # Ignora linhas problemáticas
                quoting=3  # csv.QUOTE_NONE - Desabilita completamente o uso de aspas
            )
        else:
            df = pd.read_csv(
                uploaded_file, 
                sep=delimiter,
                quotechar=None,  # Sem caractere de citação
                encoding=encoding,
                quoting=3  # csv.QUOTE_NONE - Desabilita completamente o uso de aspas
            )
        
        st.success("Arquivo carregado com sucesso!")
        
        # Exibir informações sobre o dataset
        st.subheader("Informações do dataset")
        st.write(f"Total de linhas: {df.shape[0]}")
        st.write(f"Total de colunas: {df.shape[1]}")
        
        # Exibir os dados com opções de rolagem
        st.subheader("Visualização dos dados")
        
        # Opções de visualização
        with st.expander("Opções de visualização da tabela", expanded=True):
            col1, col2 = st.columns(2)
            with col1:
                num_linhas = st.slider("Número de linhas para exibir:", 
                                   min_value=5, max_value=min(100, df.shape[0]), 
                                   value=min(20, df.shape[0]), 
                                   step=5)
                mostrar_todos = st.checkbox("Mostrar todos os dados (pode ser lento para tabelas grandes)", value=False)
            
            with col2:
                # Opções de filtragem simples
                filtrar_dados = st.checkbox("Aplicar filtro de texto", value=False)
                if filtrar_dados:
                    filtro_coluna = st.selectbox("Selecione a coluna para filtrar:", df.columns.tolist())
                    filtro_texto = st.text_input("Digite o texto para filtrar (case insensitive):")
                    
                    if filtro_texto:
                        # Aplicar filtro (case insensitive)
                        df = df[df[filtro_coluna].astype(str).str.lower().str.contains(filtro_texto.lower())]
                        st.write(f"Mostrando {df.shape[0]} linhas após aplicar o filtro.")
                        
                # Opção de ordenação
                ordenar_dados = st.checkbox("Ordenar dados", value=False)
                if ordenar_dados:
                    ordenar_coluna = st.selectbox("Ordenar pela coluna:", df.columns.tolist())
                    ordem_ascendente = st.radio("Ordem:", ("Crescente", "Decrescente")) == "Crescente"
                    df = df.sort_values(by=ordenar_coluna, ascending=ordem_ascendente)
                
                # Botão para download dos dados
                csv = df.to_csv(index=False, sep=';')
                st.download_button(
                    label="Baixar dados como CSV",
                    data=csv,
                    file_name="dados_exportados.csv",
                    mime="text/csv",
                )
        
        # Determinar quais dados mostrar
        if mostrar_todos:
            data_to_show = df
            st.write(f"Mostrando todas as {df.shape[0]} linhas e {df.shape[1]} colunas.")
        else:
            data_to_show = df.head(num_linhas)
            st.write(f"Mostrando {num_linhas} de {df.shape[0]} linhas.")
        
        # Opção para escolher entre visualização compacta ou expandida
        modo_visualizacao = st.radio("Modo de visualização:", ("Compacto", "Expandido"), horizontal=True)
        
        if modo_visualizacao == "Compacto":
            # Exibir a tabela com opção de rolagem (modo compacto)
            st.dataframe(
                data_to_show,
                use_container_width=True,  # Usa a largura total do container
                height=min(400, 35 * len(data_to_show) + 38),  # Altura dinâmica baseada no número de linhas (35px por linha + cabeçalho)
                hide_index=False  # Mostra os índices para referência
            )
        else:
            # Modo expandido - melhor para ver todos os dados com rolagem horizontal
            st.write("Modo expandido (use a barra de rolagem para ver todas as colunas):")
            st.write(data_to_show.style.set_properties(**{'text-align': 'left'}))
        
        # Adicionar visualização detalhada de linhas específicas
        with st.expander("Visualizar linha específica em detalhe"):
            if df.shape[0] > 0:
                linha_selecionada = st.number_input(
                    "Selecione o número da linha para visualizar em detalhe:", 
                    min_value=0, 
                    max_value=df.shape[0]-1, 
                    value=0,
                    step=1
                )
                
                # Mostrar os dados da linha selecionada
                st.write(f"### Detalhes da linha {linha_selecionada}")
                for coluna, valor in df.iloc[linha_selecionada].items():
                    st.text_input(coluna, value=str(valor), disabled=True)
        
        # Diagnóstico do CSV
        with st.expander("Diagnóstico do arquivo CSV"):
            st.write("Esta seção ajuda a identificar problemas no arquivo CSV.")
            
            # Verificar número de campos por linha
            num_campos = df.shape[1]
            st.write(f"Número esperado de campos por linha: {num_campos}")
            
            # Mostrar estrutura das linhas
            max_linhas = min(10, df.shape[0])
            st.write(f"Visualização das primeiras {max_linhas} linhas:")
            for i in range(max_linhas):
                st.text(f"Linha {i+1}: {len(df.iloc[i].values)} campos")
        
        # Ignorar as duas primeiras colunas
        colunas = df.columns[2:]
        if len(colunas) > 0:
            # Dropdown para selecionar a coluna (pergunta)
            coluna_selecionada = st.selectbox("Selecione a pergunta (coluna) para análise:", colunas)
            
            # Parâmetros do gráfico
            st.subheader("Opções do gráfico")
            
            col1, col2 = st.columns(2)
            with col1:
                n_palavras = st.slider("Número de palavras mais frequentes:", 5, 50, 20)
                
                # Opção para inverter a ordem das cores
                inverter_cores = st.checkbox("Inverter ordem das cores", value=False)
                
                # Tamanho do gráfico
                altura_grafico = st.slider("Altura do gráfico (px):", 400, 1000, 600, 50)
                
            with col2:
                # Opções de paletas de cores
                paleta_cores = st.selectbox(
                    "Esquema de cores:",
                    options=["Viridis", "Plasma", "Inferno", "Magma", "Cividis", 
                             "Rainbow", "Jet", "Turbo", "Blues", "Greens", "Reds",
                             "YlOrRd", "YlGnBu", "PuRd", "RdPu", "Spectral", "RdYlBu"],
                    index=0
                )
                
                # Cor do nó principal
                cor_no_principal = st.color_picker("Cor do nó principal:", "#1f77b4")
                
                # Opacidade das ligações
                opacidade = st.slider("Opacidade das ligações:", 0.3, 1.0, 0.8, 0.1)
            
            # Botão para gerar o gráfico
            if st.button("Gerar Gráfico de Sankey"):
                with st.spinner("Gerando gráfico..."):
                    # Gerar gráfico
                    textos = df[coluna_selecionada].dropna().tolist()
                    
                    # Criar mapeamento de paletas de cores
                    import plotly.colors as pc
                    import plotly.express as px
                    
                    paletas_disponiveis = {
                        "Viridis": pc.sequential.Viridis,
                        "Plasma": pc.sequential.Plasma,
                        "Inferno": pc.sequential.Inferno,
                        "Magma": pc.sequential.Magma,
                        "Cividis": pc.sequential.Cividis,
                        "Rainbow": pc.sequential.Rainbow,
                        "Jet": pc.sequential.Jet,
                        "Turbo": pc.sequential.Turbo,
                        "Blues": pc.sequential.Blues,
                        "Greens": pc.sequential.Greens,
                        "Reds": pc.sequential.Reds,
                        "YlOrRd": pc.sequential.YlOrRd,
                        "YlGnBu": pc.sequential.YlGnBu,
                        "PuRd": pc.sequential.PuRd,
                        "RdPu": pc.sequential.RdPu,
                        "Spectral": px.colors.diverging.Spectral,
                        "RdYlBu": px.colors.diverging.RdYlBu
                    }
                    
                    # Usar a paleta selecionada pelo usuário
                    colorscale = paletas_disponiveis.get(paleta_cores, pc.sequential.Viridis)
                    
                    # Inverter a escala de cores se solicitado
                    if inverter_cores:
                        colorscale = colorscale[::-1]
                    
                    # Passar todos os parâmetros para a função de criação do gráfico
                    fig = criar_grafico_sankey(
                        textos, 
                        n_palavras=n_palavras, 
                        colorscale=colorscale,
                        cor_no_principal=cor_no_principal,
                        opacidade=opacidade,
                        altura=altura_grafico
                    )
                    
                    if fig is not None:
                        # Exibir o gráfico
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Exibir contagem de palavras
                        todas_palavras = []
                        for texto in textos:
                            todas_palavras.extend(extrair_palavras(texto))
                        contador = Counter(todas_palavras)
                        
                        st.subheader("Frequência de palavras")
                        freq_df = pd.DataFrame(contador.most_common(n_palavras), columns=['Palavra', 'Frequência'])
                        st.dataframe(freq_df)
                    else:
                        st.warning("Não foi possível extrair palavras significativas dos textos.")
        else:
            st.warning("O arquivo CSV tem menos de 3 colunas. Certifique-se de que o arquivo está no formato correto.")
    
    except Exception as e:
        st.error(f"Erro ao processar o arquivo: {e}")
        st.info("""
        **Dicas para resolver problemas com CSV:**
        
        1. **Erro de tokenização** (como 'Expected 16 fields, saw 24'):
           - Verifique se nenhum campo contém ponto e vírgula (;), já que esse é o separador de colunas
           - Verifique se todas as linhas têm exatamente o mesmo número de campos (colunas)
           - Configuramos a aplicação para não exigir aspas em nenhum campo
        
        2. **Problemas de encoding**:
           - Tente diferentes encodings nas opções avançadas (latin1, ISO-8859-1, cp1252)
           
        3. **Arquivo muito grande ou complexo**:
           - Marque a opção "Ignorar linhas problemáticas"
        
        4. **Outras soluções**:
           - Abra o arquivo em um editor como Excel e salve novamente como CSV usando ponto e vírgula como separador
           - Remova manualmente caracteres especiais ou linhas problemáticas
           - Use um programa como Notepad++ para verificar e corrigir o arquivo
        """)
else:
    st.info("Por favor, faça upload de um arquivo CSV para começar.")
    
    # Fornecer um modelo de CSV para download
    st.subheader("Modelo de CSV")
    st.write("Se estiver tendo problemas com o formato do seu arquivo CSV, você pode baixar um modelo de exemplo:")
    
    modelo_csv = """id;data;O que você achou do atendimento?;Como você avalia nossos produtos?;Você recomendaria nossos serviços?
1;2025-10-01;O atendimento foi excelente, os funcionários são atenciosos.;Os produtos têm ótima qualidade.;Sim, com certeza.
2;2025-10-02;Fui bem atendido, mas demorou um pouco.;Gostei dos produtos.;Talvez.
3;2025-10-03;Atendimento rápido e eficiente.;Produtos atendem às expectativas.;Sim.
"""
    
    st.download_button(
        label="Baixar modelo de CSV",
        data=modelo_csv,
        file_name="modelo_csv.csv",
        mime="text/csv",
    )
    
    st.markdown("""
    **Dicas para formatação do CSV:**
    
    1. Não use ponto e vírgula (;) dentro do texto dos campos, pois isso confundirá o parser
    2. Verifique se todas as linhas têm o mesmo número de campos
    3. As duas primeiras colunas serão ignoradas na análise
    4. Certifique-se de que seu arquivo usa ponto e vírgula (;) como separador de colunas
    5. Não é necessário usar aspas duplas (") para delimitar os campos
    """)

# Instruções de uso
with st.expander("Como usar esta aplicação"):
    st.markdown("""
    1. Faça upload de um arquivo CSV contendo seus dados de perguntas e respostas
    2. As duas primeiras colunas serão ignoradas
    3. Selecione a coluna (pergunta) que deseja analisar no menu suspenso
    4. Ajuste o número de palavras mais frequentes que deseja visualizar
    5. Clique em 'Gerar Gráfico de Sankey'
    
    O gráfico mostrará a frequência das palavras mais comuns na coluna selecionada.
    
    **Observação**: Palavras muito curtas (menos de 3 letras) e palavras comuns (como artigos e preposições) são automaticamente filtradas.
    """)

# Rodapé
st.sidebar.markdown("---")
st.sidebar.info("Desenvolvido com Streamlit, NLTK e Plotly")