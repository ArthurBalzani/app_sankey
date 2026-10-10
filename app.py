"""
Streamlit application for word frequency analysis with Sankey diagrams.

Supports uploading multiple CSV files and selecting several question columns.
The Sankey shows questions (left) → unique words (right), with shared word nodes.
"""

from collections import Counter
from typing import Dict, List, Tuple

import pandas as pd
import streamlit as st

import config
from src.color_utils import convert_color_to_hex
from src import (
    apply_native_label_styles,
    build_sankey_diagram,
    create_word_frequency_dataframe,
    ensure_style_state,
    get_color_palette,
    needs_pinned_node_positions,
    make_content_key,
    parse_custom_stopwords,
    reset_style_customizations,
    node_id_for_question,
    resolve_plotly_node_colors,
    resolve_plotly_link_colors,
    default_question_color_for_index,
)


st.set_page_config(
    page_title=config.PAGE_TITLE,
    layout=config.PAGE_LAYOUT,
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
        [data-testid="stSidebar"],
        [data-testid="stSidebarCollapsedControl"] {
            display: none !important;
        }
    </style>
    """,
    unsafe_allow_html=True,
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
    option_id is always unique for widgets (includes file when multi-file).
    """
    multi_file = len(datasets) > 1
    options: List[Tuple[str, str, str]] = []
    for file_name, df in datasets.items():
        question_cols = list(df.columns[config.IGNORED_COLUMNS :])
        for col in question_cols:
            opt_id = f"{file_name}::{col}" if multi_file else str(col)
            options.append((opt_id, file_name, str(col)))
    return options


def _question_labels(
    options: List[Tuple[str, str, str]],
) -> Dict[str, str]:
    """
    Map option_id → display/Sankey label.

    Default: column name only. If the same column name appears in more than
    one file, append a minimal file suffix for those entries only.
    """
    col_counts = Counter(col for _, _, col in options)
    labels: Dict[str, str] = {}
    for opt_id, file_name, column in options:
        if col_counts[column] > 1:
            labels[opt_id] = f"{column} ({file_name})"
        else:
            labels[opt_id] = column
    return labels


def _build_question_texts(
    selected_ids: List[str],
    id_to_meta: Dict[str, Tuple[str, str]],
    label_by_id: Dict[str, str],
    datasets: Dict[str, pd.DataFrame],
) -> Dict[str, List[str]]:
    question_texts: Dict[str, List[str]] = {}
    used_labels: Dict[str, int] = {}
    for opt_id in selected_ids:
        file_name, column = id_to_meta[opt_id]
        label = label_by_id[opt_id]
        if label in used_labels:
            used_labels[label] += 1
            label = f"{label} ({used_labels[label]})"
        else:
            used_labels[label] = 1
        series = datasets[file_name][column]
        question_texts[label] = series.dropna().tolist()
    return question_texts


def _truncate_label(label: str, max_len: int = 48) -> str:
    if len(label) <= max_len:
        return label
    return f"{label[: max_len - 1]}…"


def _sankey_labels_for_selection(
    selected_ids: List[str],
    label_by_id: Dict[str, str],
) -> List[str]:
    labels: List[str] = []
    used: Dict[str, int] = {}
    for opt_id in selected_ids:
        label = label_by_id[opt_id]
        if label in used:
            used[label] += 1
            label = f"{label} ({used[label]})"
        else:
            used[label] = 1
        labels.append(label)
    return labels


def _render_sankey_chart(
    question_texts: Dict[str, List[str]],
    *,
    n_words: int,
    colorscale_name: str,
    invert: bool,
    opacity: float,
    chart_height: int,
    custom_stop_words: List[str],
    style_state: dict,
) -> bool:
    colorscale = get_color_palette(colorscale_name, invert)
    stop_words = set(custom_stop_words) if custom_stop_words else None

    pin_positions = needs_pinned_node_positions(style_state)

    draft = build_sankey_diagram(
        question_texts,
        n_words=n_words,
        colorscale=colorscale,
        opacity=opacity,
        height=chart_height,
        custom_stop_words=stop_words,
        hide_native_labels=False,
        pin_node_positions=pin_positions,
    )
    if draft is None:
        st.warning("Não foi possível extrair palavras significativas dos textos.")
        return False

    node_colors = resolve_plotly_node_colors(
        state=style_state,
        question_labels=draft["questions"],
        word_labels=draft["words"],
        palette_colors=colorscale,
        opacity=opacity,
        word_totals=draft["word_totals"],
    )
    sankey_trace = draft["figure"].data[0]
    link_colors = resolve_plotly_link_colors(
        state=style_state,
        question_labels=draft["questions"],
        link_sources=list(sankey_trace.link.source),
        link_targets=list(sankey_trace.link.target),
        word_labels=draft["words"],
        palette_colors=colorscale,
        word_totals=draft["word_totals"],
        opacity=opacity,
    )
    result = build_sankey_diagram(
        question_texts,
        n_words=n_words,
        colorscale=colorscale,
        opacity=opacity,
        height=chart_height,
        custom_stop_words=stop_words,
        hide_native_labels=False,
        node_colors=node_colors,
        link_colors=link_colors,
        pin_node_positions=pin_positions,
    )
    assert result is not None
    st.session_state["sankey_nodes"] = result["nodes"]
    apply_native_label_styles(result["figure"], result["nodes"], style_state)
    st.plotly_chart(result["figure"], width="stretch")

    st.subheader("Frequência de palavras")
    freq_df = create_word_frequency_dataframe(
        question_texts,
        n_words=n_words,
        custom_stop_words=stop_words,
    )
    st.dataframe(freq_df, width="stretch")
    return True


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

        st.dataframe(
            data_to_show,
            width="stretch",
            height=min(400, 35 * len(data_to_show) + 38),
            hide_index=False,
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

        if not options:
            st.warning(
                "Nenhuma coluna de pergunta encontrada. "
                "O CSV precisa de pelo menos 3 colunas "
                "(2 metadados + perguntas)."
            )
        else:
            id_to_meta = {opt_id: (fname, col) for opt_id, fname, col in options}
            label_by_id = _question_labels(options)

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

            custom_stop_words: List[str] = []
            with st.expander("Filtrar palavras irrelevantes", expanded=False):
                user_stop_words = st.text_area(
                    "Palavras a ignorar (vírgula, espaço ou linha)",
                    value="",
                    height=100,
                    label_visibility="collapsed",
                )
                custom_stop_words = parse_custom_stopwords(user_stop_words)
                if custom_stop_words:
                    st.caption(
                        f"{len(custom_stop_words)} palavra(s) personalizada(s) ignorada(s)."
                    )

            n_words = st.slider(
                "Palavras mais frequentes no gráfico",
                min_value=config.MIN_N_WORDS,
                max_value=config.MAX_N_WORDS,
                value=config.DEFAULT_N_WORDS,
            )

            color_palette = config.DEFAULT_COLOR_PALETTE
            invert_colors = False
            opacity = config.DEFAULT_OPACITY
            chart_height = config.DEFAULT_CHART_HEIGHT

            content_key = make_content_key(
                file_names=list(datasets.keys()),
                selected_question_ids=list(selected_ids),
                n_words=n_words,
                stopwords=sorted(custom_stop_words) if custom_stop_words else [],
            )
            prior_style = st.session_state.get("sankey_style")
            prior_content_key = (
                prior_style.get("content_key") if isinstance(prior_style, dict) else None
            )
            style_state = ensure_style_state(prior_style, content_key)
            if prior_content_key is not None and prior_content_key != content_key:
                st.session_state.pop("sankey_last", None)
                st.session_state.pop("sankey_nodes", None)
            st.session_state["sankey_style"] = style_state

            style_widget_gen = st.session_state.get("sankey_style_widget_gen", 0)
            style_widget_key = f"{content_key}_{style_widget_gen}"

            per_q_colors: Dict[str, str] = {}
            label_font = style_state["defaults"]["questions"]["font"]
            label_size = int(style_state["defaults"]["questions"]["size"])
            label_color = style_state["defaults"]["questions"]["color"]

            if not selected_ids:
                st.info("Selecione pelo menos uma pergunta para gerar o gráfico.")
            else:
                st.divider()
                st.markdown("### Estilo do Sankey")

                _pal_key = f"sankey_palette_{style_widget_key}"
                _inv_key = f"sankey_invert_{style_widget_key}"
                _op_key = f"sankey_opacity_{style_widget_key}"
                _ht_key = f"sankey_height_{style_widget_key}"
                if _pal_key in st.session_state:
                    color_palette = st.session_state[_pal_key]
                if _inv_key in st.session_state:
                    invert_colors = bool(st.session_state[_inv_key])
                if _op_key in st.session_state:
                    opacity = float(st.session_state[_op_key])
                if _ht_key in st.session_state:
                    chart_height = int(st.session_state[_ht_key])
                palette_for_defaults = get_color_palette(
                    color_palette, invert_colors
                )
                sankey_question_labels = _sankey_labels_for_selection(
                    selected_ids, label_by_id
                )

                n_q = len(sankey_question_labels)
                question_node_color = convert_color_to_hex(
                    style_state.get(
                        "question_node_color", config.DEFAULT_QUESTION_NODE_COLOR
                    )
                )
                per_q_colors: Dict[str, str] = {}
                with st.expander(
                    "Perguntas e ligações",
                    expanded=(n_q >= 2),
                ):
                    if n_q == 1:
                        st.caption(
                            "Cor do nó da pergunta; com uma pergunta as ligações usam a paleta. "
                            "Cores por pergunta quando há mais de uma."
                        )
                        question_node_color = st.color_picker(
                            "Cor do nó da pergunta",
                            question_node_color,
                            key=f"sankey_q_link_{style_widget_key}",
                            help=(
                                "Cor do nó da pergunta; com uma pergunta as ligações usam a paleta. "
                                "Cores por pergunta quando há mais de uma."
                            ),
                        )
                    else:
                        st.caption(
                            "Escolha uma cor por pergunta; cada ligação usa a cor da pergunta de origem."
                        )
                        per_q_colors = dict(
                            style_state.get("question_node_colors") or {}
                        )
                        for i, qlabel in enumerate(sankey_question_labels):
                            raw = per_q_colors.get(qlabel)
                            if raw is None:
                                default_q = default_question_color_for_index(
                                    i, n_q, palette_for_defaults
                                )
                            else:
                                default_q = convert_color_to_hex(raw)
                            nid = node_id_for_question(qlabel)
                            per_q_colors[qlabel] = st.color_picker(
                                f"Cor da pergunta e das ligações — {_truncate_label(qlabel)}",
                                default_q,
                                key=f"sankey_q_link_{nid}_{style_widget_key}",
                                help="Cor do nó da pergunta e de todas as fitas que saem dela.",
                            )

                with st.expander("Rótulos", expanded=False):
                    label_font = st.selectbox(
                        "Fonte dos rótulos",
                        options=config.SANKEY_FONT_FAMILIES,
                        index=config.SANKEY_FONT_FAMILIES.index(
                            style_state["defaults"]["questions"]["font"]
                        )
                        if style_state["defaults"]["questions"]["font"]
                        in config.SANKEY_FONT_FAMILIES
                        else 0,
                        key=f"sankey_label_font_{style_widget_key}",
                        help="Mesma fonte e tamanho para perguntas e palavras (limite do Plotly).",
                    )
                    label_size = st.slider(
                        "Tamanho dos rótulos",
                        min_value=8,
                        max_value=32,
                        value=int(style_state["defaults"]["questions"]["size"]),
                        key=f"sankey_label_size_{style_widget_key}",
                    )
                    label_color = st.color_picker(
                        "Cor do texto dos rótulos",
                        style_state["defaults"]["questions"]["color"],
                        key=f"sankey_label_color_{style_widget_key}",
                    )

                with st.expander("Layout e paleta", expanded=False):
                    color_palette = st.selectbox(
                        "Paleta Plotly (nós de palavra e cores padrão)",
                        options=config.COLOR_PALETTES,
                        index=config.COLOR_PALETTES.index(
                            config.DEFAULT_COLOR_PALETTE
                        ),
                        key=f"sankey_palette_{style_widget_key}",
                    )
                    invert_colors = st.checkbox(
                        "Inverter ordem da paleta",
                        value=False,
                        key=f"sankey_invert_{style_widget_key}",
                    )
                    opacity = st.slider(
                        "Opacidade das ligações",
                        0.3,
                        1.0,
                        config.DEFAULT_OPACITY,
                        0.1,
                        key=f"sankey_opacity_{style_widget_key}",
                    )
                    chart_height = st.slider(
                        "Altura do gráfico (px)",
                        min_value=config.MIN_CHART_HEIGHT,
                        max_value=config.MAX_CHART_HEIGHT,
                        value=config.DEFAULT_CHART_HEIGHT,
                        step=config.SLIDER_HEIGHT_STEP,
                        key=f"sankey_height_{style_widget_key}",
                    )

                label_fields = {
                    "font": label_font,
                    "size": label_size,
                    "color": label_color,
                }
                style_state["defaults"]["questions"] = dict(label_fields)
                style_state["defaults"]["words"] = dict(label_fields)
                if n_q == 1:
                    style_state["question_node_color"] = question_node_color
                    style_state["question_node_colors"] = {}
                else:
                    style_state["question_node_colors"] = per_q_colors
                    style_state["question_node_color"] = next(
                        iter(per_q_colors.values())
                    )
                st.session_state["sankey_style"] = style_state

                btn_gen, btn_reset = st.columns([3, 1])
                with btn_gen:
                    generate = st.button(
                        "Gerar gráfico de Sankey",
                        type="primary",
                        width="stretch",
                    )
                with btn_reset:
                    if st.button("Resetar estilo", width="stretch"):
                        st.session_state["sankey_style"] = (
                            reset_style_customizations(style_state)
                        )
                        st.session_state["sankey_style_widget_gen"] = (
                            style_widget_gen + 1
                        )
                        st.rerun()

                if generate:
                    question_texts = _build_question_texts(
                        selected_ids, id_to_meta, label_by_id, datasets
                    )
                    st.session_state["sankey_last"] = {
                        "question_texts": question_texts,
                        "n_words": n_words,
                        "colorscale_name": color_palette,
                        "invert": invert_colors,
                        "opacity": opacity,
                        "height": chart_height,
                        "custom_stop_words": sorted(custom_stop_words)
                        if custom_stop_words
                        else [],
                    }

            last = st.session_state.get("sankey_last")
            if last and selected_ids:
                with st.spinner("Atualizando gráfico..."):
                    _render_sankey_chart(
                        last["question_texts"],
                        n_words=last["n_words"],
                        colorscale_name=last["colorscale_name"],
                        invert=last["invert"],
                        opacity=last["opacity"],
                        chart_height=last["height"],
                        custom_stop_words=last["custom_stop_words"],
                        style_state=st.session_state["sankey_style"],
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
        - **Delimitador:** padrão `;` (ponto e vírgula). Não coloque esse caractere dentro dos textos das respostas.
        - **Colunas:** todas as linhas devem ter o mesmo número de colunas.
        - **Metadados:** as **duas primeiras colunas** de cada arquivo são ignoradas na análise (ex.: id e data); a partir da 3ª coluna entram as **perguntas** (cabeçalho = enunciado).
        - **Vários arquivos:** envie um ou mais CSVs e selecione perguntas de qualquer um no mesmo gráfico.
        - **Encoding:** se o upload falhar, use *Opções avançadas de importação* para testar latin1, ISO-8859-1 ou cp1252.
        - **Modelo:** use o botão de download acima se precisar de um exemplo válido.
        """
        )

with st.expander("❓ Como usar esta aplicação"):
    st.markdown(
        """
    ### Passos
    1. Envie **um ou mais** arquivos CSV.
    2. Ignore mentalmente as **2 primeiras colunas** (metadados); escolha **perguntas** (colunas) para analisar.
    3. Ajuste filtros (top N palavras, stopwords extras) e **Estilo do Sankey** (rótulos, cores, paleta, layout).
    4. Clique em **Gerar Gráfico de Sankey**.
    5. Depois de gerar, mudar fonte, cores ou paleta **atualiza o gráfico** sem gerar de novo.

    ### Estilo e cores
    - **Rótulos (Plotly):** uma fonte, um tamanho e uma cor de texto para todos os nós.
    - **1 pergunta:** cor do nó da pergunta em *Perguntas e ligações*; **ligações** seguem a paleta por frequência das palavras.
    - **2+ perguntas:** uma cor por pergunta — vale para o **nó** e para as **ligações** que saem dela.
    - **Nós de palavra:** cores automáticas pela paleta Plotly (sem controle separado de cor).

    ### Gráfico
    - **Esquerda:** cada pergunta selecionada vira um nó.
    - **Direita:** palavras únicas (a mesma palavra em várias perguntas compartilha um nó).
    - **Ligações:** espessura = frequência da palavra **naquela** pergunta.
    - **Arrastar nós:** o Plotly permite reposicionar nós no diagrama (só nesta sessão).

    ### Filtros de texto
    - Palavras com menos de 3 letras e stopwords em português (lista padrão).
    - Lista extra de palavras a ignorar, se quiser, antes de gerar.
    """
    )
