"""
Streamlit application for word frequency analysis with Sankey diagrams.

This application allows uploading a CSV file and generating a Sankey diagram
visualizing the frequency of the most common words in selected columns.
"""

import streamlit as st
import pandas as pd

import config
from src import (
    create_sankey_diagram,
    create_word_frequency_dataframe,
    get_color_palette,
    parse_custom_stopwords
)


# Page configuration
st.set_page_config(
    page_title=config.PAGE_TITLE,
    layout=config.PAGE_LAYOUT
)

# Title
st.title("Gerador de Gráfico Sankey para Frequência de Palavras")
# ============================================================================
# CSV File Upload and Processing
# ============================================================================

uploaded_file = st.file_uploader("Faça upload do arquivo CSV", type=config.CSV_ALLOWED_TYPES)

if uploaded_file is not None:
    try:
        # User options
        with st.expander("Opções avançadas de importação"):
            delimiter = st.text_input("Delimitador", value=config.DEFAULT_DELIMITER)
            encoding = st.selectbox("Encoding", config.SUPPORTED_ENCODINGS, index=0)
            error_bad_lines = st.checkbox("Ignorar linhas problemáticas", value=True)
            
        # Show processing message
        processing_info = st.info("Tentando processar o arquivo...")
            
        # Try to load the file with the specified options
        try:
            if error_bad_lines:
                df = pd.read_csv(
                    uploaded_file, 
                    sep=delimiter,
                    encoding=encoding,
                    on_bad_lines='skip',
                    quoting=3
                )
            else:
                df = pd.read_csv(
                    uploaded_file, 
                    sep=delimiter,
                    encoding=encoding,
                    quoting=3
                )
        except Exception as read_error:
            processing_info.empty()
            st.error(f"Erro ao ler o arquivo: {read_error}")
            raise
        
        # Remove processing message and show success
        processing_info.empty()
        st.success("Arquivo carregado com sucesso!")
        
        # Display information about the dataset
        st.subheader("Informações do dataset")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total de linhas", df.shape[0])
        with col2:
            st.metric("Total de colunas", df.shape[1])
        
        # ====================================================================
        # Data Visualization Options
        # ====================================================================
        st.subheader("Visualização dos dados")
        
        with st.expander("Opções de visualização da tabela", expanded=True):
            col1, col2 = st.columns(2)
            
            with col1:
                max_rows_value = max(6, min(100, df.shape[0]))
                num_rows = st.slider(
                    "Número de linhas para exibir:",
                    min_value=1, max_value=max_rows_value,
                    value=min(20, df.shape[0]),
                    step=1
                )
                show_all = st.checkbox("Mostrar todos os dados (pode ser lento para tabelas grandes)", value=False)
            
            with col2:
                # Filtering options
                filter_data = st.checkbox("Aplicar filtro de texto", value=False)
                if filter_data:
                    filter_column = st.selectbox("Selecione a coluna para filtrar:", df.columns.tolist())
                    filter_text = st.text_input("Digite o texto para filtrar (case insensitive):")
                    
                    if filter_text:
                        df = df[df[filter_column].astype(str).str.lower().str.contains(filter_text.lower())]
                        st.write(f"Mostrando {df.shape[0]} linhas após aplicar o filtro.")
                
                # Sorting option
                sort_data = st.checkbox("Ordenar dados", value=False)
                if sort_data:
                    sort_column = st.selectbox("Ordenar pela coluna:", df.columns.tolist())
                    ascending_order = st.radio("Ordem:", ("Crescente", "Decrescente")) == "Crescente"
                    df = df.sort_values(by=sort_column, ascending=ascending_order)
                
                # Download button
                csv = df.to_csv(index=False, sep=config.DEFAULT_DELIMITER)
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
        
        # View mode selection
        view_mode = st.radio("Modo de visualização:", ("Compacto", "Expandido"), horizontal=True)
        
        if view_mode == "Compacto":
            st.dataframe(
                data_to_show,
                use_container_width=True,
                height=min(400, 35 * len(data_to_show) + 38),
                hide_index=False
            )
        else:
            st.write("Modo expandido (use a barra de rolagem para ver todas as colunas):")
            st.write(data_to_show.style.set_properties(subset=None, **{'text-align': 'left'}))
        
        # Detailed row view
        with st.expander("Visualizar linha específica em detalhe"):
            if df.shape[0] > 0:
                selected_row = st.number_input(
                    "Selecione o número da linha para visualizar em detalhe:",
                    min_value=0,
                    max_value=df.shape[0]-1,
                    value=0,
                    step=1
                )
                
                st.write(f"### Detalhes da linha {selected_row}")
                for column, value in df.iloc[selected_row].items():
                    st.text_input(str(column), value=str(value), disabled=True)
        
        # CSV diagnostics
        with st.expander("Diagnóstico do arquivo CSV"):
            st.write("Esta seção ajuda a identificar problemas no arquivo CSV.")
            num_fields = df.shape[1]
            st.write(f"Número esperado de campos por linha: {num_fields}")
            
            max_rows = min(10, df.shape[0])
            st.write(f"Visualização das primeiras {max_rows} linhas:")
            for i in range(max_rows):
                st.text(f"Linha {i+1}: {len(df.iloc[i].values)} campos")
        
        # ====================================================================
        # Analysis Section
        # ====================================================================
        columns = df.columns[config.IGNORED_COLUMNS:]
        
        if len(columns) > 0:
            selected_column = st.selectbox("Selecione a pergunta (coluna) para análise:", columns)
            
            st.subheader("Opções do gráfico")
            
            # Custom stopwords
            with st.expander("Filtrar palavras irrelevantes", expanded=False):
                st.markdown("**Adicione palavras que você deseja excluir da análise:**")
                user_stop_words = st.text_area(
                    "Digite as palavras separadas por vírgula, espaço ou nova linha:",
                    value="",
                    height=100,
                    help="Estas palavras serão adicionadas à lista de stopwords"
                )
                
                custom_stop_words = parse_custom_stopwords(user_stop_words)
                if custom_stop_words:
                    st.info(f"Serão ignoradas {len(custom_stop_words)} palavras personalizadas")
            
            # Chart parameters
            col1, col2 = st.columns(2)
            
            with col1:
                n_words = st.slider(
                    "Número de palavras mais frequentes:",
                    min_value=config.MIN_N_WORDS,
                    max_value=config.MAX_N_WORDS,
                    value=config.DEFAULT_N_WORDS
                )
                
                invert_colors = st.checkbox("Inverter ordem das cores", value=False)
                
                chart_height = st.slider(
                    "Altura do gráfico (px):",
                    min_value=config.MIN_CHART_HEIGHT,
                    max_value=config.MAX_CHART_HEIGHT,
                    value=config.DEFAULT_CHART_HEIGHT,
                    step=config.SLIDER_HEIGHT_STEP
                )
            
            with col2:
                color_palette = st.selectbox(
                    "Esquema de cores:",
                    options=config.COLOR_PALETTES,
                    index=config.COLOR_PALETTES.index(config.DEFAULT_COLOR_PALETTE)
                )
                
                main_node_color = st.color_picker("Cor do nó principal:", config.DEFAULT_MAIN_NODE_COLOR)
                
                opacity = st.slider("Opacidade das ligações:", 0.3, 1.0, config.DEFAULT_OPACITY, 0.1)
            
            # Generate chart button
            if st.button("Gerar Gráfico de Sankey", use_container_width=True):
                with st.spinner("Gerando gráfico..."):
                    # Get texts
                    texts = df[selected_column].dropna().tolist()
                    
                    # Get color palette
                    colorscale = get_color_palette(color_palette, invert_colors)
                    
                    # Create Sankey diagram
                    fig = create_sankey_diagram(
                        texts,
                        n_words=n_words,
                        colorscale=colorscale,
                        main_node_color=main_node_color,
                        opacity=opacity,
                        height=chart_height,
                        custom_stop_words=custom_stop_words if custom_stop_words else None
                    )
                    
                    if fig is not None:
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Display word frequency table
                        st.subheader("Frequência de palavras")
                        freq_df = create_word_frequency_dataframe(
                            texts,
                            n_words=n_words,
                            custom_stop_words=custom_stop_words if custom_stop_words else None
                        )
                        st.dataframe(freq_df, use_container_width=True)
                    else:
                        st.warning("Não foi possível extrair palavras significativas dos textos.")
        else:
            st.warning("O arquivo CSV tem menos de 3 colunas. Certifique-se de que o arquivo está no formato correto.")
    
    except Exception as e:
        st.error(f"Erro ao processar o arquivo: {e}")
        with st.expander("💡 Dicas para resolver problemas com CSV"):
            st.markdown("""
            **1. Erro de tokenização** (ex: 'Expected 16 fields, saw 24'):
            - Verifique se nenhum campo contém o caractere delimitador escolhido (padrão: `;`)
            - Verifique se todas as linhas têm exatamente o mesmo número de colunas
            
            **2. Problemas de encoding**:
            - Tente diferentes encodings (latin1, ISO-8859-1, cp1252)
            
            **3. Arquivo muito grande ou complexo**:
            - Marque "Ignorar linhas problemáticas"
            
            **4. Outras soluções**:
            - Abra em Excel e salve como CSV
            - Use Notepad++ para verificar caracteres especiais
            """)

else:
    st.info("📤 Por favor, faça upload de um arquivo CSV para começar.")
    
    # CSV template
    st.subheader("Modelo de CSV")
    st.write("Baixe um modelo de exemplo se estiver tendo problemas de formato:")
    
    csv_template = """id;data;O que você achou do atendimento?;Como você avalia nossos produtos?;Você recomendaria nossos serviços?
1;2025-10-01;O atendimento foi excelente, os funcionários são atenciosos.;Os produtos têm ótima qualidade.;Sim, com certeza.
2;2025-10-02;Fui bem atendido, mas demorou um pouco.;Gostei dos produtos.;Talvez.
3;2025-10-03;Atendimento rápido e eficiente.;Produtos atendem às expectativas.;Sim.
"""
    
    st.download_button(
        label="📥 Baixar modelo de CSV",
        data=csv_template,
        file_name="modelo_csv.csv",
        mime="text/csv",
    )
    
    with st.expander("ℹ️ Dicas para formatação do CSV"):
        st.markdown("""
        1. Não use o caractere delimitador (padrão: `;`) dentro dos campos
        2. Verifique se todas as linhas têm o mesmo número de colunas
        3. As duas primeiras colunas serão ignoradas na análise
        4. Use ponto e vírgula (`;`) como separador padrão
        """)

# ============================================================================
# Usage Instructions
# ============================================================================
with st.expander("❓ Como usar esta aplicação"):
    st.markdown("""
    ### Passos:
    1. Faça upload de um arquivo CSV contendo dados
    2. As 2 primeiras colunas serão ignoradas
    3. Selecione a coluna (pergunta) para análise
    4. Ajuste as opções do gráfico conforme desejado
    5. Clique em **'Gerar Gráfico de Sankey'**
    
    ### O que o gráfico mostra:
    - **Nó central**: A fonte ("Pergunta")
    - **Linhas**: Conexões entre a pergunta e cada palavra
    - **Espessura**: Proporcional à frequência da palavra
    - **Cores**: Representam a frequência relativa
    
    ### Filtros automáticos:
    - Palavras muito curtas (< 3 letras)
    - Palavras comuns (artigos, preposições, etc)
    """)

# Footer
st.sidebar.markdown("---")
st.sidebar.markdown("""
    
    **Desenvolvido com:**
    - [Streamlit](https://streamlit.io)
    - [Plotly](https://plotly.com)
    - [NLTK](https://www.nltk.org)
    - [Pandas](https://pandas.pydata.org)
    
""")
