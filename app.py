"""
Tableau SUS — Exploração visual de dados do SUS (estilo Tableau) com PyGWalker + Streamlit.

Faça upload de planilhas .xlsx (ou .csv no padrão brasileiro) e explore os dados
com uma interface de arrastar-e-soltar (drag-and-drop), sem escrever código.

Stack: Streamlit + PyGWalker (Graphic Walker), pandas, openpyxl.
"""

from __future__ import annotations

import hashlib
from io import BytesIO
from pathlib import Path

import pandas as pd
import streamlit as st
from pygwalker.api.streamlit import StreamlitRenderer

# ---------------------------------------------------------------------------
# Configuração da página
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Tableau SUS",
    page_icon="📊",
    layout="wide",
)

SPEC_DIR = Path("gw_specs")
SPEC_DIR.mkdir(exist_ok=True)


# ---------------------------------------------------------------------------
# Leitura de arquivos (cacheada por conteúdo do arquivo)
# ---------------------------------------------------------------------------
def file_signature(file_bytes: bytes) -> str:
    """Identificador curto e estável a partir do conteúdo do arquivo."""
    return hashlib.md5(file_bytes).hexdigest()[:12]


@st.cache_data(show_spinner=False)
def list_excel_sheets(file_bytes: bytes) -> list[str]:
    return pd.ExcelFile(BytesIO(file_bytes)).sheet_names


@st.cache_data(show_spinner=False)
def read_excel_sheet(file_bytes: bytes, sheet_name: str) -> pd.DataFrame:
    return pd.read_excel(BytesIO(file_bytes), sheet_name=sheet_name)


@st.cache_data(show_spinner=False)
def read_csv_br(
    file_bytes: bytes,
    sep: str,
    encoding: str,
    decimal: str,
    thousands: str,
) -> pd.DataFrame:
    return pd.read_csv(
        BytesIO(file_bytes),
        sep=sep,
        encoding=encoding,
        decimal=decimal,
        thousands=thousands or None,
    )


# ---------------------------------------------------------------------------
# Renderer do PyGWalker (cacheado por dataset, não recria a cada interação)
# ---------------------------------------------------------------------------
@st.cache_resource(show_spinner=False)
def get_renderer(cache_key: str, _df: pd.DataFrame, use_duckdb: bool) -> StreamlitRenderer:
    """
    O `_df` começa com underscore para o Streamlit NÃO tentar gerar hash dele.
    O `cache_key` (assinatura do arquivo + aba + modo) é quem controla o cache:
    o renderer só é recriado quando o dataset realmente muda.
    """
    spec_path = SPEC_DIR / f"{cache_key}.json"
    return StreamlitRenderer(
        _df,
        spec=str(spec_path),
        spec_io_mode="rw",            # permite salvar a config dos gráficos pela UI
        kernel_computation=use_duckdb,  # DuckDB para datasets grandes
    )


# ---------------------------------------------------------------------------
# Barra lateral — fonte de dados
# ---------------------------------------------------------------------------
st.sidebar.title("📊 Tableau SUS")
st.sidebar.caption("Exploração visual de dados do SUS — estilo Tableau, sem código.")

uploaded = st.sidebar.file_uploader(
    "Envie uma planilha",
    type=["xlsx", "xls", "csv"],
    help="Excel (.xlsx/.xls) ou CSV. Para CSV no padrão brasileiro, ajuste as opções abaixo.",
)

use_duckdb = st.sidebar.toggle(
    "Modo alto desempenho (DuckDB)",
    value=False,
    help="Use o DuckDB como motor de cálculo para explorar datasets grandes mais rápido.",
)

# ---------------------------------------------------------------------------
# Tela inicial (sem arquivo)
# ---------------------------------------------------------------------------
if uploaded is None:
    st.title("Tableau SUS")
    st.markdown(
        """
        Bem-vindo(a). Esta página transforma qualquer planilha numa interface de
        **análise visual no estilo Tableau**, com arrastar-e-soltar.

        **Como usar**
        1. No menu à esquerda, envie um arquivo **.xlsx** (ou **.csv**).
        2. Se for Excel com várias abas, escolha a aba desejada.
        3. Arraste os campos para linhas, colunas, cor, tamanho etc. e monte seus gráficos.
        4. Clique em **salvar** dentro do explorador para guardar a configuração dos gráficos.

        Os dados ficam **apenas na sua sessão** — nada é gravado de forma permanente no servidor.
        """
    )
    st.info("Envie uma planilha na barra lateral para começar.", icon="⬅️")
    st.stop()

# ---------------------------------------------------------------------------
# Leitura do arquivo enviado
# ---------------------------------------------------------------------------
file_bytes = uploaded.getvalue()
sig = file_signature(file_bytes)
is_excel = uploaded.name.lower().endswith((".xlsx", ".xls"))

if is_excel:
    sheets = list_excel_sheets(file_bytes)
    sheet = st.sidebar.selectbox("Aba (planilha)", sheets, index=0)
    df = read_excel_sheet(file_bytes, sheet)
    cache_key = f"{sig}-{sheet}-{int(use_duckdb)}"
    source_label = f"{uploaded.name} · aba “{sheet}”"
else:
    st.sidebar.markdown("**Opções de CSV (padrão brasileiro)**")
    sep = st.sidebar.selectbox("Separador", [";", ",", "\\t", "|"], index=0)
    sep = "\t" if sep == "\\t" else sep
    encoding = st.sidebar.selectbox("Codificação", ["latin-1", "utf-8", "cp1252"], index=0)
    decimal = st.sidebar.selectbox("Separador decimal", [",", "."], index=0)
    thousands = st.sidebar.selectbox("Separador de milhar", [".", ",", "(nenhum)"], index=0)
    thousands = "" if thousands == "(nenhum)" else thousands
    df = read_csv_br(file_bytes, sep, encoding, decimal, thousands)
    cache_key = f"{sig}-{sep}-{encoding}-{decimal}-{thousands}-{int(use_duckdb)}"
    source_label = uploaded.name

# ---------------------------------------------------------------------------
# Cabeçalho + resumo do dataset
# ---------------------------------------------------------------------------
st.title("Tableau SUS")
st.caption(f"Fonte: {source_label}")

c1, c2, c3 = st.columns(3)
c1.metric("Linhas", f"{len(df):,}".replace(",", "."))
c2.metric("Colunas", f"{df.shape[1]}")
c3.metric("Motor de cálculo", "DuckDB" if use_duckdb else "pandas")

with st.expander("Prévia dos dados (10 primeiras linhas)"):
    st.dataframe(df.head(10), use_container_width=True)

# ---------------------------------------------------------------------------
# Explorador PyGWalker
# ---------------------------------------------------------------------------
renderer = get_renderer(cache_key, df, use_duckdb)
renderer.explorer()

# ---------------------------------------------------------------------------
# Salvar / restaurar a configuração dos gráficos
# ---------------------------------------------------------------------------
with st.expander("💾 Salvar / restaurar configuração dos gráficos"):
    st.markdown(
        "No **Streamlit Community Cloud** o disco é temporário: a configuração salva "
        "pela UI some quando o app reinicia. Baixe o arquivo abaixo para guardar seus "
        "gráficos e reenvie depois para restaurá-los."
    )
    spec_path = SPEC_DIR / f"{cache_key}.json"
    if spec_path.exists():
        st.download_button(
            "Baixar configuração (.json)",
            data=spec_path.read_bytes(),
            file_name=f"tableau_sus_{sig}.json",
            mime="application/json",
        )
    else:
        st.caption("Ainda não há configuração salva. Monte um gráfico e clique em salvar no explorador.")

    restore = st.file_uploader("Restaurar configuração (.json)", type=["json"], key="restore_spec")
    if restore is not None:
        spec_path.write_bytes(restore.getvalue())
        st.cache_resource.clear()
        st.success("Configuração restaurada. Recarregando…")
        st.rerun()
