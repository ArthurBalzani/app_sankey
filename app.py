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
import matplotlib.colors as mcolors  # For color conversion

# Page configuration
st.set_page_config(page_title="Análise de Frequência de Palavras", layout="wide")

# Title
st.title("Gerador de Gráfico Sankey para Frequência de Palavras")

# Function to extract significant words from text
@st.cache_data
def extract_words(text, custom_stop_words=None):
    if pd.isna(text):
        return []
    
    try:
        # Ensure we have stopwords
        nltk.download('stopwords', quiet=True)
        stop_words = set(stopwords.words('portuguese'))
        
        # Add additional common stopwords in Portuguese
        additional_stop_words = {'pra', 'pro', 'sobre', 'assim', 'então', 'porque', 
                               'muito', 'muita', 'muitos', 'muitas', 'bem', 'mal',
                               'sim', 'não', 'pelo', 'pela', 'pelos', 'pelas'}
        stop_words.update(additional_stop_words)
        
        # Add custom stop words from user input if available
        if custom_stop_words:
            stop_words.update(custom_stop_words)
            
    except:
        stop_words = set()  # If it fails, use an empty set
    
    # Ensure text is string
    text_str = str(text).lower()
    
    # Normalization - remove accents
    import unicodedata
    text_norm = unicodedata.normalize('NFKD', text_str)
    text_norm = ''.join([c for c in text_norm if not unicodedata.combining(c)])
    
    # Remove punctuation and convert to lowercase
    words = re.findall(r'\b\w+\b', text_norm)
    
    # Filter stopwords and words with less than 3 characters
    words = [p for p in words if p not in stop_words and len(p) > 2]
    return words

# Function to create Sankey diagram
def create_sankey_diagram(texts, n_words=20, colorscale=None, main_node_color="#1f77b4", 
                         opacity=0.8, height=600, custom_stop_words=None):
    all_words = []
    for text in texts:
        all_words.extend(extract_words(text, custom_stop_words))
    
    # Count frequency
    counter = Counter(all_words)
    
    # If there are no words, return None
    if not counter:
        return None
    
    # Get the N most common words
    common_words = dict(counter.most_common(n_words))
    
    # Prepare data for the Sankey diagram
    nodes_labels = ["Pergunta"]  # Source node
    nodes_labels.extend(common_words.keys())  # Target nodes (words)
    
    source = []
    target = []
    value = []
    
    # Connections between "Pergunta" and words
    source_idx = 0  # Index of the "Pergunta" node
    for i, (word, freq) in enumerate(common_words.items(), 1):
        source.append(source_idx)
        target.append(i)
        value.append(freq)
    
    # Define different colors for each connection
    import plotly.colors as pc
    
    # Use the provided color palette or Viridis as default
    if colorscale is None:
        colorscale = pc.sequential.Viridis
    
    # List to store colors for each connection
    colors = []
    node_colors = []
    
    # Create a list of frequency values to normalize colors
    freq_values = list(common_words.values())
    max_freq = max(freq_values) if freq_values else 1
    
    # Convert main_node_color from hex to rgba if necessary
    if main_node_color.startswith("#"):
        from matplotlib.colors import to_rgba
        rgba = to_rgba(main_node_color)
        main_node_color = f"rgba({int(rgba[0]*255)}, {int(rgba[1]*255)}, {int(rgba[2]*255)}, {opacity})"
    
    # Generate colors for each connection based on relative frequency
    for i, (word, freq) in enumerate(common_words.items()):
        # Normalize the frequency to get a value between 0 and 1
        normalized_freq = freq / max_freq
        # Get color from the color scale
        color_base = pc.sample_colorscale(colorscale, normalized_freq)[0]
        
        # If the color is in hex format, convert to rgba to apply opacity
        if color_base.startswith("#"):
            from matplotlib.colors import to_rgba
            rgba = to_rgba(color_base)
            color = f"rgba({int(rgba[0]*255)}, {int(rgba[1]*255)}, {int(rgba[2]*255)}, {opacity})"
        elif color_base.startswith("rgb("):
            # Convert from rgb to rgba
            color_base = color_base.replace("rgb(", "").replace(")", "")
            r, g, b = map(int, color_base.split(","))
            color = f"rgba({r}, {g}, {b}, {opacity})"
        else:
            # Already rgba, just adjust opacity
            color = color_base
        
        colors.append(color)
        node_colors.append(color)
    
    # Create Sankey diagram with custom colors
    fig = go.Figure(data=[go.Sankey(
        node = dict(
            pad = 15,
            thickness = 20,
            line = dict(color = "black", width = 0.5),
            label = nodes_labels,
            # Color nodes with corresponding colors
            color = [main_node_color] + node_colors
        ),
        link = dict(
            source = source,
            target = target,
            value = value,
            color = colors  # Each connection with its specific color
        )
    )])
    
    fig.update_layout(
        title_text="Frequência de palavras na pergunta selecionada",
        font_size=12,
        height=height,  # Customizable height
        # Improving overall layout
        margin=dict(l=25, r=25, t=50, b=25),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
    
    return fig

# CSV file upload
uploaded_file = st.file_uploader("Faça upload do arquivo CSV", type=['csv'])

if uploaded_file is not None:
    # Load data
    try:
        # User options
        with st.expander("Opções avançadas de importação"):
            delimiter = st.text_input("Delimitador", value=";")  # Semicolon as default
            encoding = st.selectbox("Encoding", ["utf-8", "latin1", "ISO-8859-1", "cp1252"], index=0)
            error_bad_lines = st.checkbox("Ignorar linhas problemáticas", value=True)
            
        # Show processing message
        processing_info = st.info("Tentando processar o arquivo...")
            
        # Try to load the file with the specified options
        if error_bad_lines:
            df = pd.read_csv(
                uploaded_file, 
                sep=delimiter,
                quotechar=None,  # No quote character
                encoding=encoding,
                on_bad_lines='skip',  # Skip problematic lines
                quoting=3  # csv.QUOTE_NONE - Completely disable quotes
            )
        else:
            df = pd.read_csv(
                uploaded_file, 
                sep=delimiter,
                quotechar=None,  # No quote character
                encoding=encoding,
                quoting=3  # csv.QUOTE_NONE - Completely disable quotes
            )
        
        # Remove processing message and show success
        processing_info.empty()
        st.success("Arquivo carregado com sucesso!")
        
        # Display information about the dataset
        st.subheader("Informações do dataset")
        st.write(f"Total de linhas: {df.shape[0]}")
        st.write(f"Total de colunas: {df.shape[1]}")
        
        # Display data with scrolling options
        st.subheader("Visualização dos dados")
        
        # Visualization options
        with st.expander("Opções de visualização da tabela", expanded=True):
            col1, col2 = st.columns(2)
            with col1:
                num_rows = st.slider("Número de linhas para exibir:", 
                                   min_value=5, max_value=min(100, df.shape[0]), 
                                   value=min(20, df.shape[0]), 
                                   step=5)
                show_all = st.checkbox("Mostrar todos os dados (pode ser lento para tabelas grandes)", value=False)
            
            with col2:
                # Simple filtering options
                filter_data = st.checkbox("Aplicar filtro de texto", value=False)
                if filter_data:
                    filter_column = st.selectbox("Selecione a coluna para filtrar:", df.columns.tolist())
                    filter_text = st.text_input("Digite o texto para filtrar (case insensitive):")
                    
                    if filter_text:
                        # Apply filter (case insensitive)
                        df = df[df[filter_column].astype(str).str.lower().str.contains(filter_text.lower())]
                        st.write(f"Mostrando {df.shape[0]} linhas após aplicar o filtro.")
                        
                # Sorting option
                sort_data = st.checkbox("Ordenar dados", value=False)
                if sort_data:
                    sort_column = st.selectbox("Ordenar pela coluna:", df.columns.tolist())
                    ascending_order = st.radio("Ordem:", ("Crescente", "Decrescente")) == "Crescente"
                    df = df.sort_values(by=sort_column, ascending=ascending_order)
                
                # Botão para download dos dados
                csv = df.to_csv(index=False, sep=';')
                st.download_button(
                    label="Baixar dados como CSV",
                    data=csv,
                    file_name="dados_exportados.csv",
                    mime="text/csv",
                )
        
        # Determine which data to show
        if show_all:
            data_to_show = df
            st.write(f"Mostrando todas as {df.shape[0]} linhas e {df.shape[1]} colunas.")
        else:
            data_to_show = df.head(num_rows)
            st.write(f"Mostrando {num_rows} de {df.shape[0]} linhas.")
        
        # Option to choose between compact or expanded view
        view_mode = st.radio("Modo de visualização:", ("Compacto", "Expandido"), horizontal=True)
        
        if view_mode == "Compacto":
            # Display the table with scrolling option (compact mode)
            st.dataframe(
                data_to_show,
                use_container_width=True,  # Use full container width
                height=min(400, 35 * len(data_to_show) + 38),  # Dynamic height based on number of rows (35px per row + header)
                hide_index=False  # Show indices for reference
            )
        else:
            # Expanded mode - better for viewing all data with horizontal scrolling
            st.write("Modo expandido (use a barra de rolagem para ver todas as colunas):")
            st.write(data_to_show.style.set_properties(**{'text-align': 'left'}))
        
        # Add detailed view of specific rows
        with st.expander("Visualizar linha específica em detalhe"):
            if df.shape[0] > 0:
                selected_row = st.number_input(
                    "Selecione o número da linha para visualizar em detalhe:", 
                    min_value=0, 
                    max_value=df.shape[0]-1, 
                    value=0,
                    step=1
                )
                
                # Show the selected row data
                st.write(f"### Detalhes da linha {selected_row}")
                for column, value in df.iloc[selected_row].items():
                    st.text_input(column, value=str(value), disabled=True)
        
        # CSV diagnostics
        with st.expander("Diagnóstico do arquivo CSV"):
            st.write("Esta seção ajuda a identificar problemas no arquivo CSV.")
            
            # Check number of fields per line
            num_fields = df.shape[1]
            st.write(f"Número esperado de campos por linha: {num_fields}")
            
            # Show line structure
            max_rows = min(10, df.shape[0])
            st.write(f"Visualização das primeiras {max_rows} linhas:")
            for i in range(max_rows):
                st.text(f"Linha {i+1}: {len(df.iloc[i].values)} campos")
        
        # Ignore the first two columns
        columns = df.columns[2:]
        if len(columns) > 0:
            # Dropdown to select the column (question)
            selected_column = st.selectbox("Selecione a pergunta (coluna) para análise:", columns)
            
            # Chart parameters
            st.subheader("Opções do gráfico")
            
            # Palavras para filtrar
            with st.expander("Filtrar palavras irrelevantes", expanded=False):
                st.markdown("**Adicione palavras que você deseja excluir da análise:**")
                user_stop_words = st.text_area(
                    "Digite as palavras separadas por vírgula, espaço ou nova linha:",
                    value="",
                    height=100,
                    help="Estas palavras serão adicionadas à lista de stopwords e não aparecerão no gráfico"
                )
                
                # Processar as palavras inseridas pelo usuário
                if user_stop_words:
                    # Separar palavras por vírgula, espaço ou quebra de linha
                    custom_stop_words = set(word.strip().lower() for word in re.split(r'[,\s]+', user_stop_words) if word.strip())
                    st.info(f"Serão ignoradas {len(custom_stop_words)} palavras personalizadas: {', '.join(sorted(custom_stop_words))}")
                else:
                    custom_stop_words = set()
            
            col1, col2 = st.columns(2)
            with col1:
                n_words = st.slider("Número de palavras mais frequentes:", 5, 50, 20)
                
                # Option to invert color order
                invert_colors = st.checkbox("Inverter ordem das cores", value=False)
                
                # Chart size
                chart_height = st.slider("Altura do gráfico (px):", 400, 1000, 600, 50)
                
            with col2:
                # Color palette options
                color_palette = st.selectbox(
                    "Esquema de cores:",
                    options=["Viridis", "Plasma", "Inferno", "Magma", "Cividis", 
                             "Rainbow", "Jet", "Turbo", "Blues", "Greens", "Reds",
                             "YlOrRd", "YlGnBu", "PuRd", "RdPu", "Spectral", "RdYlBu"],
                    index=0
                )
                
                # Main node color
                main_node_color = st.color_picker("Cor do nó principal:", "#1f77b4")
                
                # Link opacity
                opacity = st.slider("Opacidade das ligações:", 0.3, 1.0, 0.8, 0.1)
            
            # Button to generate the chart
            if st.button("Gerar Gráfico de Sankey"):
                with st.spinner("Gerando gráfico..."):
                    # Generate chart
                    texts = df[selected_column].dropna().tolist()
                    
                    # Create color palette mapping
                    import plotly.colors as pc
                    import plotly.express as px
                    
                    available_palettes = {
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
                    
                    # Use the palette selected by the user
                    colorscale = available_palettes.get(color_palette, pc.sequential.Viridis)
                    
                    # Invert the color scale if requested
                    if invert_colors:
                        colorscale = colorscale[::-1]
                    
                    # Pass all parameters to the chart creation function
                    fig = create_sankey_diagram(
                        texts, 
                        n_words=n_words, 
                        colorscale=colorscale,
                        main_node_color=main_node_color,
                        opacity=opacity,
                        height=chart_height,
                        custom_stop_words=custom_stop_words if 'custom_stop_words' in locals() else None
                    )
                    
                    if fig is not None:
                        # Display the chart
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Display word count
                        all_words = []
                        for text in texts:
                            all_words.extend(extract_words(text, custom_stop_words if 'custom_stop_words' in locals() else None))
                        counter = Counter(all_words)
                        
                        st.subheader("Frequência de palavras")
                        freq_df = pd.DataFrame(counter.most_common(n_words), columns=['Palavra', 'Frequência'])
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
    
    # Provide a CSV template for download
    st.subheader("Modelo de CSV")
    st.write("Se estiver tendo problemas com o formato do seu arquivo CSV, você pode baixar um modelo de exemplo:")
    
    csv_template = """id;data;O que você achou do atendimento?;Como você avalia nossos produtos?;Você recomendaria nossos serviços?
1;2025-10-01;O atendimento foi excelente, os funcionários são atenciosos.;Os produtos têm ótima qualidade.;Sim, com certeza.
2;2025-10-02;Fui bem atendido, mas demorou um pouco.;Gostei dos produtos.;Talvez.
3;2025-10-03;Atendimento rápido e eficiente.;Produtos atendem às expectativas.;Sim.
"""
    
    st.download_button(
        label="Baixar modelo de CSV",
        data=csv_template,
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

# Footer
st.sidebar.markdown("---")
st.sidebar.info("Desenvolvido com Streamlit, NLTK e Plotly")