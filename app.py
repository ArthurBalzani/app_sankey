"""
Streamlit application for word frequency analysis with Sankey diagrams.

Supports uploading multiple CSV files and selecting several question columns.
The Sankey shows questions (left) → unique words (right), with shared word nodes.
"""

from typing import Dict, List, Tuple

import pandas as pd
import streamlit as st

import config
from src import (
    create_sankey_diagram,
    create_word_frequency_dataframe,
    get_color_palette,
    parse_custom_stopwords,
)


st.set_page_config(
    page_title=config.PAGE_TITLE,
    layout=config.PAGE_LAYOUT,
)

st.title("Gerador de Gráfico Sankey para Frequência de Palavras")


def _read_csv(uploaded_file, delimiter: str, encoding: str, skip_bad: bool) -> pd.DataFrame:
    kwargs = dict(sep=delimiter, encoding=encoding, quoting=3)
    if skip_bad:
        kwargs["on_bad_lines"] = "skip"
    return pd.read_csv(uploaded_file, **kwargs)


def _question_options(
    datasets: Dict[str, pd.DataFrame],
) -> List[Tuple[str, str, str]]:
    """
    Build selectable questions across files.

    Returns list of (option_id, file_name, column_name).
    option_id is unique for widgets; display uses file + column when multi-file.
    """
    multi_file = len(datasets) > 1
    options: List[Tuple[str, str, str]] = []
    for file_name, df in datasets.items():
        question_cols = list(df.columns[config.IGNORED_COLUMNS :])
        for col in question_cols:
            opt_id = f"{file_name}::{col}" if multi_file else str(col)
            options.append((opt_id, file_name, str(col)))
    return options


def _display_label(opt_id: str, file_name: str, column: str, multi_file: bool) -> str:
    if multi_file:
        return f"{file_name} → {column}"
    return column


uploaded_files = st.file_uploader(
    "Faça upload de um ou mais arquivos CSV",
    type=config.CSV_ALLOWED_TYPES,
    accept_multiple_files=True,
)

if uploaded_files:
    try:
        with st.expander("Opções avançadas de importação"):
            delimiter = st.text_input("Delimitador", value=config.DEFAULT_DELIMITER)
            encoding = st.selectbox("Encoding", config.SUPPORTED_ENCODINGS, index=0)
            error_bad_lines = st.checkbox("Ignorar linhas problemáticas", value=True)

        processing_info = st.info("Processando arquivos...")
        datasets: Dict[str, pd.DataFrame] = {}
        load_errors: List[str] = []

        for uploaded in uploaded_files:
            name = uploaded.name
            try:
                uploaded.seek(0)
                datasets[name] = _read_csv(
                    uploaded, delimiter, encoding, error_bad_lines
                )
            except Exception as read_error:
                load_errors.append(f"{name}: {read_error}")

        processing_info.empty()

        if load_errors:
            for err in load_errors:
                st.error(f"Erro ao ler arquivo: {err}")

        if not datasets:
            st.warning("Nenhum arquivo pôde ser carregado.")
            st.stop()

        st.success(
            f"{len(datasets)} arquivo(s) carregado(s) com sucesso!"
            if len(datasets) > 1
            else "Arquivo carregado com sucesso!"
        )

        st.subheader("Informações dos datasets")
        metric_cols = st.columns(min(4, max(1, len(datasets))))
        for i, (name, df) in enumerate(datasets.items()):
            with metric_cols[i % len(metric_cols)]:
                st.metric(name, f"{df.shape[0]}×{df.shape[1]}")

        st.subheader("Visualização dos dados")
        file_names = list(datasets.keys())
        preview_file = (
            st.selectbox("Arquivo para visualizar:", file_names)
            if len(file_names) > 1
            else file_names[0]
        )
        df = datasets[preview_file]

        with st.expander("Opções de visualização da tabela", expanded=True):
            col1, col2 = st.columns(2)

            with col1:
                max_rows_value = max(6, min(100, df.shape[0]))
                num_rows = st.slider(
                    "Número de linhas para exibir:",
                    min_value=1,
                    max_value=max_rows_value,
                    value=min(20, df.shape[0]),
                    step=1,
                )
                show_all = st.checkbox(
                    "Mostrar todos os dados (pode ser lento para tabelas grandes)",
                    value=False,
                )

            with col2:
                filter_data = st.checkbox("Aplicar filtro de texto", value=False)
                preview_df = df
                if filter_data:
                    filter_column = st.selectbox(
                        "Selecione a coluna para filtrar:", df.columns.tolist()
                    )
                    filter_text = st.text_input(
                        "Digite o texto para filtrar (case insensitive):"
                    )
                    if filter_text:
                        preview_df = df[
                            df[filter_column]
                            .astype(str)
                            .str.lower()
                            .str.contains(filter_text.lower())
                        ]
                        st.write(
                            f"Mostrando {preview_df.shape[0]} linhas após aplicar o filtro."
                        )

                sort_data = st.checkbox("Ordenar dados", value=False)
                if sort_data:
                    sort_column = st.selectbox(
                        "Ordenar pela coluna:", preview_df.columns.tolist()
                    )
                    ascending_order = (
                        st.radio("Ordem:", ("Crescente", "Decrescente")) == "Crescente"
                    )
                    preview_df = preview_df.sort_values(
                        by=sort_column, ascending=ascending_order
                    )

                csv = preview_df.to_csv(index=False, sep=config.DEFAULT_DELIMITER)
                st.download_button(
                    label="Baixar dados como CSV",
                    data=csv,
                    file_name="dados_exportados.csv",
                    mime="text/csv",
                )

        data_to_show = preview_df if show_all else preview_df.head(num_rows)
        if show_all:
            st.write(
                f"Mostrando todas as {preview_df.shape[0]} linhas e "
                f"{preview_df.shape[1]} colunas."
            )
        else:
            st.write(f"Mostrando {num_rows} de {preview_df.shape[0]} linhas.")

        view_mode = st.radio(
            "Modo de visualização:", ("Compacto", "Expandido"), horizontal=True
        )
        if view_mode == "Compacto":
            st.dataframe(
                data_to_show,
                use_container_width=True,
                height=min(400, 35 * len(data_to_show) + 38),
                hide_index=False,
            )
        else:
            st.write(
                "Modo expandido (use a barra de rolagem para ver todas as colunas):"
            )
            st.write(
                data_to_show.style.set_properties(
                    subset=None, **{"text-align": "left"}
                )
            )

        with st.expander("Visualizar linha específica em detalhe"):
            if preview_df.shape[0] > 0:
                selected_row = st.number_input(
                    "Selecione o número da linha para visualizar em detalhe:",
                    min_value=0,
                    max_value=preview_df.shape[0] - 1,
                    value=0,
                    step=1,
                )
                st.write(f"### Detalhes da linha {selected_row}")
                for column, value in preview_df.iloc[selected_row].items():
                    st.text_input(str(column), value=str(value), disabled=True)

        with st.expander("Diagnóstico do arquivo CSV"):
            st.write("Esta seção ajuda a identificar problemas no arquivo CSV.")
            st.write(f"Arquivo: **{preview_file}**")
            st.write(f"Número esperado de campos por linha: {df.shape[1]}")
            max_rows = min(10, df.shape[0])
            st.write(f"Visualização das primeiras {max_rows} linhas:")
            for i in range(max_rows):
                st.text(f"Linha {i + 1}: {len(df.iloc[i].values)} campos")

        # ====================================================================
        # Analysis — multi question selection
        # ====================================================================
        options = _question_options(datasets)
        multi_file = len(datasets) > 1

        if not options:
            st.warning(
                "Nenhuma coluna de pergunta encontrada. "
                "O CSV precisa de pelo menos 3 colunas "
                "(2 metadados + perguntas)."
            )
        else:
            id_to_meta = {opt_id: (fname, col) for opt_id, fname, col in options}
            label_by_id = {
                opt_id: _display_label(opt_id, fname, col, multi_file)
                for opt_id, fname, col in options
            }

            default_selection = [options[0][0]]
            selected_ids = st.multiselect(
                "Selecione as perguntas (colunas) para análise:",
                options=[opt_id for opt_id, _, _ in options],
                default=default_selection,
                format_func=lambda oid: label_by_id[oid],
                help=(
                    "Cada pergunta vira um nó à esquerda. "
                    "Palavras iguais entre perguntas compartilham o mesmo nó à direita."
                ),
            )

            st.subheader("Opções do gráfico")

            with st.expander("Filtrar palavras irrelevantes", expanded=False):
                st.markdown(
                    "**Adicione palavras que você deseja excluir da análise:**"
                )
                user_stop_words = st.text_area(
                    "Digite as palavras separadas por vírgula, espaço ou nova linha:",
                    value="",
                    height=100,
                    help="Estas palavras serão adicionadas à lista de stopwords",
                )
                custom_stop_words = parse_custom_stopwords(user_stop_words)
                if custom_stop_words:
                    st.info(
                        f"Serão ignoradas {len(custom_stop_words)} palavras personalizadas"
                    )

            col1, col2 = st.columns(2)

            with col1:
                n_words = st.slider(
                    "Número de palavras mais frequentes:",
                    min_value=config.MIN_N_WORDS,
                    max_value=config.MAX_N_WORDS,
                    value=config.DEFAULT_N_WORDS,
                )
                invert_colors = st.checkbox("Inverter ordem das cores", value=False)
                chart_height = st.slider(
                    "Altura do gráfico (px):",
                    min_value=config.MIN_CHART_HEIGHT,
                    max_value=config.MAX_CHART_HEIGHT,
                    value=config.DEFAULT_CHART_HEIGHT,
                    step=config.SLIDER_HEIGHT_STEP,
                )

            with col2:
                color_palette = st.selectbox(
                    "Esquema de cores:",
                    options=config.COLOR_PALETTES,
                    index=config.COLOR_PALETTES.index(config.DEFAULT_COLOR_PALETTE),
                )
                main_node_color = st.color_picker(
                    "Cor do nó da pergunta (origem):",
                    config.DEFAULT_MAIN_NODE_COLOR,
                )
                opacity = st.slider(
                    "Opacidade das ligações:",
                    0.3,
                    1.0,
                    config.DEFAULT_OPACITY,
                    0.1,
                )

            if not selected_ids:
                st.info("Selecione pelo menos uma pergunta para gerar o gráfico.")
            elif st.button("Gerar Gráfico de Sankey", use_container_width=True):
                with st.spinner("Gerando gráfico..."):
                    question_texts: Dict[str, List[str]] = {}
                    used_labels: Dict[str, int] = {}

                    for opt_id in selected_ids:
                        file_name, column = id_to_meta[opt_id]
                        label = label_by_id[opt_id]
                        # Ensure unique left-node labels if collision
                        if label in used_labels:
                            used_labels[label] += 1
                            label = f"{label} ({used_labels[label]})"
                        else:
                            used_labels[label] = 1

                        series = datasets[file_name][column]
                        question_texts[label] = series.dropna().tolist()

                    colorscale = get_color_palette(color_palette, invert_colors)

                    fig = create_sankey_diagram(
                        question_texts,
                        n_words=n_words,
                        colorscale=colorscale,
                        main_node_color=main_node_color,
                        opacity=opacity,
                        height=chart_height,
                        custom_stop_words=(
                            custom_stop_words if custom_stop_words else None
                        ),
                    )

                    if fig is not None:
                        st.plotly_chart(fig, use_container_width=True)

                        st.subheader("Frequência de palavras")
                        freq_df = create_word_frequency_dataframe(
                            question_texts,
                            n_words=n_words,
                            custom_stop_words=(
                                custom_stop_words if custom_stop_words else None
                            ),
                        )
                        st.dataframe(freq_df, use_container_width=True)
                    else:
                        st.warning(
                            "Não foi possível extrair palavras significativas dos textos."
                        )

    except Exception as e:
        st.error(f"Erro ao processar o arquivo: {e}")
        with st.expander("💡 Dicas para resolver problemas com CSV"):
            st.markdown(
                """
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
            """
            )

else:
    st.info("📤 Faça upload de um ou mais arquivos CSV para começar.")

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
        st.markdown(
            """
        1. Não use o caractere delimitador (padrão: `;`) dentro dos campos
        2. Verifique se todas as linhas têm o mesmo número de colunas
        3. As duas primeiras colunas serão ignoradas na análise
        4. Use ponto e vírgula (`;`) como separador padrão
        5. Você pode enviar vários arquivos e combinar perguntas no mesmo gráfico
        """
        )

with st.expander("❓ Como usar esta aplicação"):
    st.markdown(
        """
    ### Passos:
    1. Faça upload de **um ou mais** arquivos CSV
    2. As 2 primeiras colunas de cada arquivo serão ignoradas
    3. Selecione uma ou mais perguntas (colunas) para análise
    4. Ajuste as opções do gráfico conforme desejado
    5. Clique em **'Gerar Gráfico de Sankey'**

    ### O que o gráfico mostra:
    - **Esquerda**: uma pergunta selecionada por nó
    - **Direita**: palavras únicas (se a mesma palavra aparece em várias perguntas, há um único nó)
    - **Fluxo**: frequência da palavra **naquela** pergunta
    - **Espessura**: proporcional à frequência
    - **Cores**: com 1 pergunta, pela frequência da palavra; com várias, pela pergunta de origem

    ### Filtros automáticos:
    - Palavras muito curtas (< 3 letras)
    - Palavras comuns (artigos, preposições, etc)
    """
    )

st.sidebar.markdown("---")
st.sidebar.markdown(
    """

    **Desenvolvido com:**
    - [Streamlit](https://streamlit.io)
    - [Plotly](https://plotly.com)
    - [NLTK](https://www.nltk.org)
    - [Pandas](https://pandas.pydata.org)

"""
)
