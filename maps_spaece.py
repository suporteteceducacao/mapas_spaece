import pandas as pd
import matplotlib.pyplot as plt
import geopandas as gpd
from matplotlib.colors import ListedColormap
import unicodedata
import streamlit as st
from io import BytesIO
from PIL import Image  # Para carregar o logotipo

# Função para normalizar strings (remover acentos e converter para maiúsculas)
def normalize_string(text):
    if isinstance(text, str):
        text = unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode('ASCII')
        text = text.upper().strip()
    return text

# Função para definir os bounds e labels com base na ETAPA e COMPONENTE CURRICULAR
def get_bounds_and_labels(etapa, componente):
    if etapa == '5º Ano' and componente == 'LÍNGUA PORTUGUESA':
        bounds = [0, 125, 175, 225, 275, 1000]
        labels = ['Até 125', '125-175', '175-225', 'Acima de 225', 'Acima de 375']
    elif etapa == '5º Ano' and componente == 'MATEMÁTICA':
        bounds = [0, 150, 200, 250, 275, 1000]
        labels = ['Até 150', '150-200', '200-250', 'Acima de 250', 'Acima de 325']
    elif etapa == '2º Ano' and componente == 'LÍNGUA PORTUGUESA':
        bounds = [0, 75, 100, 125, 150, 1000]
        labels = ['Até 75', '75-100', '100-125', 'Acima de 150', 'Acima de 175']
    elif etapa == '9º Ano' and componente == 'MATEMÁTICA':
        bounds = [0, 225, 275, 325, 375, 1000]
        labels = ['Até 225', '225-275', '275-325', 'Acima de 325', 'Acima de 335']
    elif etapa == '9º Ano' and componente == 'LÍNGUA PORTUGUESA':
        bounds = [0, 200, 250, 300, 325, 1000]
        labels = ['Até 200', '200-250', '250-300', 'Acima de 300', 'Acima de 335']
    else:
        raise ValueError("Combinação de ETAPA e COMPONENTE CURRICULAR não suportada.")
    
    return bounds, labels

# Função para definir as cores com base na ETAPA
def get_colors(etapa):
    if etapa == '2º Ano':
        colors = ['red', 'yellow', 'orange', 'lime', 'darkgreen']
    else:
        colors = ['red', 'yellow', 'lime', 'darkgreen']
    
    return colors

# Função para gerar o mapa
def generate_map(etapa, ano, componente, crede, mapa_tipo):
    # Carregar os dados
    if etapa == '2º Ano':
        df = pd.read_excel("mapas_spaece/xls/dados_alfa.xlsx")
    else:
        df = pd.read_excel("mapas_spaece/xls/dados_spaece.xlsx")
    
    # Normalizar os nomes dos municípios e outras colunas de texto
    df['MUNICIPIO'] = df['MUNICIPIO'].apply(normalize_string)
    df['ETAPA'] = df['ETAPA'].apply(normalize_string)
    df['CREDE'] = df['CREDE'].apply(normalize_string)
    df['COMPONENTE_CURRICULAR'] = df['COMPONENTE_CURRICULAR'].apply(normalize_string)
    
    # Filtrar os dados com base na ETAPA, ANO e COMPONENTE CURRICULAR
    df_filtered = df[
        (df['ETAPA'] == normalize_string(etapa)) &
        (df['ANO'] == ano) &
        (df['COMPONENTE_CURRICULAR'] == normalize_string(componente))
    ]
    
    # Verificar se há dados após o filtro
    if df_filtered.empty:
        st.error("Nenhum dado encontrado para os filtros selecionados.")
        return None
    
    # Carregar o shapefile
    gdf = gpd.read_file('mapas_spaece/CE_Municipios_2022/CE_Municipios_2022.shp')
    
    # Verificar se o shapefile foi carregado corretamente
    if gdf.empty:
        st.error("O shapefile está vazio ou não foi carregado corretamente.")
        return None
    
    # Verificar se as geometrias são válidas
    if not gdf.geometry.is_valid.all():
        gdf.geometry = gdf.geometry.buffer(0)
    
    # Normalizar os nomes dos municípios no shapefile
    gdf['NM_MUN'] = gdf['NM_MUN'].apply(normalize_string)
    
    # Filtrar os municípios da CREDE selecionada (se for o caso)
    if mapa_tipo == "CREDE":
        df_filtered = df_filtered[df_filtered['CREDE'] == normalize_string(crede)]
        crede_municipalities = df_filtered['MUNICIPIO'].unique()
        gdf = gdf[gdf['NM_MUN'].isin(crede_municipalities)]
        titulo = f'Municípios da {crede} \n Resultados SPAECE {ano} - {componente} {etapa}'
    else:
        titulo = f'Municípios do Ceará \n Resultados SPAECE {ano} - {componente} {etapa}'
    
    # Verificar se há correspondência entre os municípios do shapefile e da planilha
    if gdf.empty:
        st.error("Nenhum município correspondente encontrado entre o shapefile e a planilha.")
        return None
    
    # Merge dos dados
    gdf_merged = pd.merge(gdf, df_filtered, left_on='NM_MUN', right_on='MUNICIPIO', how='left')
    
    # Verificar e tratar valores nulos na coluna de proficiência média
    if gdf_merged['PROFICIENCIA_MEDIA'].isnull().any():
        gdf_merged['PROFICIENCIA_MEDIA'].fillna(0, inplace=True)
    
    # Definir os bounds e labels
    bounds, labels = get_bounds_and_labels(etapa, componente)
    
    # Definir as cores
    colors = get_colors(etapa)
    cmap = ListedColormap(colors)
    
    # Categorizar a coluna de proficiência média
    gdf_merged['color_category'] = pd.cut(gdf_merged['PROFICIENCIA_MEDIA'], bins=bounds, labels=labels, include_lowest=True)
    
    # Criar o mapa
    fig, ax = plt.subplots(figsize=(10, 7))  # Tamanho do mapa aumentado
    ax.set_aspect('equal')  # Força o aspecto a ser igual
    
    # Plotar o mapa
    gdf_merged.plot(column='color_category', linewidth=0.5, ax=ax, edgecolor='black', legend=True, cmap=cmap)
    
    # Remover eixos
    plt.axis('off')
    
    # Adicionar rótulos com a PROFICIENCIA_MEDIA (apenas para o mapa da CREDE)
    if mapa_tipo == "CREDE":
        for index, row in gdf_merged.iterrows():
            x, y = row['geometry'].centroid.x, row['geometry'].centroid.y
            plt.text(
                x, y,
                f"{row['PROFICIENCIA_MEDIA']:.0f}",  # Valor da proficiência média
                fontsize=8,                          # Tamanho da fonte
                ha='center',                         # Alinhamento horizontal
                va='center'                          # Alinhamento vertical
            )
    
    # Definir o título
    plt.title(titulo, fontsize=16)
    
    # Criar a legenda com tamanho maior
    legend_labels = labels
    legend_colors = [plt.cm.colors.rgb2hex(color) for color in colors]
    legend_elements = [plt.Line2D([0], [0], marker='o', color='w', markerfacecolor=color, markersize=8, label=label) for color, label in zip(legend_colors, legend_labels)]
    
    plt.legend(
    handles=legend_elements,
    title='Escala SPAECE',
    loc='lower right',  # Posição da legenda
    prop={'size': 8},  # Tamanho da fonte da legenda
    markerscale=1.3,    # Aumenta o tamanho dos marcadores na legenda
    title_fontsize=10,  # Tamanho da fonte do título da legenda
    borderpad=0.3,      # Espaçamento interno da caixa da legenda
    labelspacing=0.5    # Espaçamento entre os itens da legenda
)
    
    # Inserir a fonte com tamanho maior
    plt.suptitle(
        f"FONTE: SPAECE {ano}",
        x=0.01,          # Posição horizontal (0.01 = 1% da largura do gráfico)
        y=-0.02,         # Posição vertical (-0.02 = 2% abaixo do gráfico)
        ha="left",       # Alinhamento horizontal (left = alinhado à esquerda)
        fontsize=8     # Tamanho da fonte
    )
    
    return fig

# Configuração da página do Streamlit
st.set_page_config(
    page_title="Gerador de Mapas SPAECE",
    page_icon="🌍",
    layout="wide"
)

# Sidebar (Coluna da Esquerda)
with st.sidebar:
    # Logotipo
    st.image("mapas_spaece/img/logo_2021.png", width=200)  # Substitua "logo.png" pelo caminho da sua imagem

    # Texto explicativo
    st.markdown("""
        ## Sobre a Aplicação
        Esta aplicação permite gerar mapas coropléticos com base nos resultados do SPAECE.
        
        ### Como Utilizar
        1. Selecione a **ETAPA**, **ANO**, **COMPONENTE CURRICULAR** e **CREDE** (ou "Ceará Inteiro").
        2. Clique em **Gerar Mapa**.
        3. O mapa será exibido e poderá ser baixado em formato PNG.
    """)

# Coluna da Direita
st.title("🌍 Gerador de Mapas SPAECE")

# Listas de opções
etapas = ['2º Ano', '5º Ano', '9º Ano']
anos = [ano for ano in range(2012, 2024) if ano not in [2020, 2021]]  # Anos de 2012 a 2023, exceto 2020 e 2021
componentes = ['LÍNGUA PORTUGUESA', 'MATEMÁTICA']
credes = ['FORTALEZA', 'MARACANAU', 'ITAPIPOCA', 'ACARAU', 'CAMOCIM', 'TIANGUA', 'SOBRAL', 'CANINDE',
          'BATURITE', 'HORIZONTE', 'RUSSAS', 'JAGUARIBE', 'QUIXADA', 'CRATEUS', 'SENADOR POMPEU',
          'TAUA', 'IGUATU', 'ICO', 'CRATO', 'JUAZEIRO DO NORTE', 'BREJO SANTO']

# Seletores
col1, col2 = st.columns(2)
with col1:
    etapa = st.selectbox("ETAPA:", etapas)
    ano = st.selectbox("ANO:", anos)
    componente = st.selectbox("COMPONENTE CURRICULAR:", componentes)
with col2:
    mapa_tipo = st.radio("Selecione o tipo de mapa:", ["CREDE", "CEARÁ"])
    if mapa_tipo == "CREDE":
        crede = st.selectbox("CREDE:", credes)
    else:
        crede = None

# Botão para gerar o mapa
if st.button("Gerar Mapa"):
    fig = generate_map(etapa, ano, componente, crede, mapa_tipo)
    if fig:
        st.pyplot(fig)
        
        # Botão para download do mapa
        buf = BytesIO()
        fig.savefig(buf, format="png", bbox_inches='tight')
        buf.seek(0)
        st.download_button(
            label="Baixar Mapa (PNG)",
            data=buf,
            file_name=f"mapa_spaece_{etapa}_{ano}_{componente}_{mapa_tipo}.png",
            mime="image/png"
        )