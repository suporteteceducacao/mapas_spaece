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

# Função para carregar e mapear os nomes dos municípios
def load_municipality_names():
    # Carregar a planilha com os nomes dos municípios no formato do shapefile
    df_municipios = pd.read_excel("xls/nome_municipios_shapefile.xlsx")
    df_municipios['NM_MUN'] = df_municipios['NM_MUN'].apply(normalize_string)
    return df_municipios

# Função para verificar se os municípios estão presentes nas planilhas de dados e no shapefile
def check_municipality_names(municipios, df_municipios, df_dados):
    municipios_normalizados = [normalize_string(mun) for mun in municipios]
    municipios_faltantes = []

    for mun in municipios_normalizados:
        if mun not in df_municipios['NM_MUN'].values:
            municipios_faltantes.append(mun)
        elif mun not in df_dados['MUNICIPIO'].values:
            municipios_faltantes.append(mun)
    
    if municipios_faltantes:
        st.warning(f"Os seguintes municípios não foram encontrados nas planilhas de dados ou no shapefile: {municipios_faltantes}")
        return False
    return True

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
    elif etapa == '3ª Série EM' and componente == 'MATEMÁTICA':
        bounds = [0, 250, 300, 350, 375, 1000]
        labels = ['Até 250', '251-300', '301-350', 'Acima de 351', 'Acima de 355']
    elif etapa == '3ª Série EM' and componente == 'LÍNGUA PORTUGUESA':
        bounds = [0, 225, 275, 325, 375, 1000]
        labels = ['Até 255', '256-275', '276-325', 'Acima de 326', 'Acima de 330']
    else:
        raise ValueError("Combinação de ETAPA e COMPONENTE CURRICULAR não suportada.")
    
    return bounds, labels

# Função para definir as cores com base na ETAPA
def get_colors(etapa):
    if etapa == '2º Ano':
        colors = ['red', 'yellow', 'orange', 'lime', 'darkgreen']
    elif etapa == '3ª Série EM':
        colors = ['red', 'yellow', 'lime', 'darkgreen']
    else:
        colors = ['red', 'yellow', 'lime', 'darkgreen']
    
    return colors

# Dicionário com as regiões de planejamento e seus municípios
regioes_planejamento = {
    "CARIRI": ['Abaiara', 'Altaneira', 'Antonina do Norte', 'Araripe', 'Assaré', 'Aurora', 'Barbalha', 'Barro', 'Brejo Santo', 'Campos Sales', 'Caririaçu', 'Crato', 'Farias Brito', 'Granjeiro', 'Jardim', 'Jati', 'Juazeiro do Norte', 'Lavras da Mangabeira', 'Mauriti', 'Milagres', 'Missão Velha', 'Nova Olinda', 'Penaforte', 'Porteiras', 'Potengi', 'Salitre', 'Santana do Cariri', 'Tarrafas', 'Várzea Alegre'],
    "CENTRO-SUL": ['Acopiara', 'Baixio', 'Cariús', 'Catarina', 'Cedro', 'Icó', 'Iguatu', 'Ipaumirim', 'Jucás', 'Orós', 'Quixelô', 'Saboeiro', 'Umari'],
    "GRANDE FORTALEZA": ['Aquiraz', 'Cascavel', 'Caucaia', 'Chorozinho', 'Eusébio', 'Fortaleza', 'Guaiúba', 'Horizonte', 'Itaitinga', 'Maracanaú', 'Maranguape', 'Pacajus', 'Pacatuba', 'Paracuru', 'Paraipaba', 'Pindoretama', 'São Gonçalo do Amarante', 'São Luís do Curu', 'Trairi'],
    "LITORAL LESTE": ['Aracati', 'Beberibe', 'Fortim', 'Icapuí', 'Itaiçaba', 'Jaguaruana'],
    "LITORAL NORTE": ['Acaraú', 'Barroquinha', 'Bela Cruz', 'Camocim', 'Chaval', 'Cruz', 'Granja', 'Itarema', 'Jijoca de Jericoacoara', 'Marco', 'Martinópole', 'Morrinhos', 'Uruoca'],
    "LITORAL OESTE/VALE DO CURU": ['Amontada', 'Apuiarés', 'General Sampaio', 'Irauçuba', 'Itapajé', 'Itapipoca', 'Miraíma', 'Pentecoste', 'Tejuçuoca', 'Tururu', 'Umirim', 'Uruburetama'],
    "MACIÇO DE BATURITÉ": ['Acarape', 'Aracoiaba', 'Aratuba', 'Barreira', 'Baturité', 'Capistrano', 'Guaramiranga', 'Itapiúna', 'Mulungu', 'Ocara', 'Pacoti', 'Palmácia', 'Redenção'],
    "SERTÃO CENTRAL": ['Banabuiú', 'Choró', 'Deputado Irapuan Pinheiro', 'Ibaretama', 'Ibicuitinga', 'Milhã', 'Mombaça', 'Pedra Branca', 'Piquet Carneiro', 'Quixadá', 'Quixeramobim', 'Senador Pompeu', 'Solonópole'],
    "SERRA DA IBIAPABA": ['Carnaubal', 'Croatá', 'Guaraciaba do Norte', 'Ibiapina', 'Ipu', 'São Benedito', 'Tianguá', 'Ubajara', 'Viçosa do Ceará'],
    "SERTÃO DE CANINDÉ": ['Canindé', 'Paramoti', 'Caridade', 'Itatira', 'General Sampaio', 'Santa Quitéria'],
    "SERTÃO DE SOBRAL": ['Alcântaras', 'Cariré', 'Coreaú', 'Forquilha', 'Frecheirinha', 'Graça', 'Groaíras', 'Massapê', 'Meruoca', 'Moraújo', 'Mucambo', 'Pacujá', 'Pires Ferreira', 'Reriutaba', 'Santana do Acaraú', 'Senador Sá', 'Sobral', 'Varjota'],
    "SERTÃO DE CRATÉUS": ['Ararendá', 'Catunda', 'Crateús', 'Hidrolândia', 'Independência', 'Ipaporanga', 'Ipueiras', 'Monsenhor Tabosa', 'Nova Russas', 'Novo Oriente', 'Poranga', 'Santa Quitéria', 'Tamboril'],
    "SERTÃO DE INHAMÚS": ['Aiuaba', 'Arneiroz', 'Parambu', 'Quiterianópolis', 'Tauá'],
    "VALE DO JAGUARIBE": ['Alto Santo', 'Ererê', 'Iracema', 'Jaguaretama', 'Jaguaribara', 'Jaguaribe', 'Limoeiro do Norte', 'Morada Nova', 'Palhano', 'Pereiro', 'Potiretama', 'Quixeré', 'Russas', 'São João do Jaguaribe', 'Tabuleiro do Norte']
}

# Função para gerar o mapa
def generate_map(etapa, ano, componente, crede, mapa_tipo, mostrar_nomes):
    # Carregar os dados
    if etapa == '2º Ano':
        df = pd.read_excel("xls/dados_alfa.xlsx")
    else:
        df = pd.read_excel("xls/dados_spaece.xlsx")
    
    # Carregar os nomes dos municípios no formato do shapefile
    df_municipios = load_municipality_names()
    
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
    
    # Mapear os nomes dos municípios nas planilhas de dados para os nomes no shapefile
    df_filtered = pd.merge(df_filtered, df_municipios, left_on='MUNICIPIO', right_on='NM_MUN', how='left')
    
    # Filtrar os municípios com base no tipo de mapa selecionado
    if mapa_tipo == "CREDE":
        if crede == "CANINDÉ":
            crede_municipalities = ['Canindé', 'Paramoti', 'Caridade', 'Itatira', 'General Sampaio', 'Santa Quitéria']
        else:
            df_filtered = df_filtered[df_filtered['CREDE'] == normalize_string(crede)]
            crede_municipalities = df_filtered['NM_MUN'].unique()
        gdf = gdf[gdf['NM_MUN'].isin(crede_municipalities)]
        titulo = f'Municípios da {crede} \n Resultados SPAECE {ano} - {componente} {etapa}'
    elif mapa_tipo == "REGIÃO DE PLANEJAMENTO":
        regiao_municipalities = [normalize_string(mun) for mun in regioes_planejamento[crede]]
        # Verificar se os municípios estão presentes nas planilhas de dados e no shapefile
        if not check_municipality_names(regiao_municipalities, df_municipios, df_filtered):
            return None
        gdf = gdf[gdf['NM_MUN'].isin(regiao_municipalities)]
        titulo = f'Municípios da {crede} \n Resultados SPAECE {ano} - {componente} {etapa}'
    elif mapa_tipo == "CEARÁ":
        titulo = f'Municípios do Ceará \n Resultados SPAECE {ano} - {componente} {etapa}'
    else:
        st.error("Tipo de mapa não suportado.")
        return None
    
    # Verificar se há correspondência entre os municípios do shapefile e da planilha
    if gdf.empty:
        st.error("Nenhum município correspondente encontrado entre o shapefile e a planilha.")
        return None
    
    # Merge dos dados
    gdf_merged = pd.merge(gdf, df_filtered, left_on='NM_MUN', right_on='NM_MUN', how='left')
    
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
    
    # Adicionar rótulos com a PROFICIENCIA_MEDIA (exceto no mapa do CEARÁ)
    if mapa_tipo != "CEARÁ":
        for index, row in gdf_merged.iterrows():
            x, y = row['geometry'].centroid.x, row['geometry'].centroid.y
            plt.text(
                x, y,
                f"{row['PROFICIENCIA_MEDIA']:.0f}",  # Valor da proficiência média
                fontsize=8,                          # Tamanho da fonte
                ha='center',                         # Alinhamento horizontal
                va='center'                          # Alinhamento vertical
            )
    
    # Adicionar nomes dos municípios (se habilitado)
    if mostrar_nomes:
        for index, row in gdf_merged.iterrows():
            x, y = row['geometry'].centroid.x, row['geometry'].centroid.y
            plt.text(
                x, y + 0.02,  # Ajuste para posicionar o nome acima da proficiência
                row['NM_MUN'],  # Nome do município
                fontsize=5,     # Tamanho da fonte
                ha='center',    # Alinhamento horizontal
                va='bottom',    # Alinhamento vertical
                color='black',  # Cor do texto
                alpha=0.7       # Transparência
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
        prop={'size': 7},  # Tamanho da fonte da legenda
        markerscale=1.2,    # Aumenta o tamanho dos marcadores na legenda
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
    page_title="Gerador de Mapas Coropléticos SPAECE",
    page_icon="🌍",
    layout="wide"
)

# Sidebar (Coluna da Esquerda)
with st.sidebar:
    # Logotipo
    st.image("img/logo_2021.png", width=300)  # Substitua "logo.png" pelo caminho da sua imagem

    # Texto explicativo
    st.markdown("""
        ## Sobre a Aplicação
        Esta aplicação permite gerar mapas coropléticos com base nos resultados do SPAECE.
        
        ### Como Utilizar
        1. Selecione a **ETAPA**, **ANO**, **COMPONENTE CURRICULAR** e **TIPO DE MAPA**.
        2. Clique em **Gerar Mapa**.
        3. O mapa será exibido e poderá ser baixado em formato PNG.
    """)

# Coluna da Direita
st.title("🌍 Gerador de Mapas SPAECE")

# Listas de opções
etapas = ['2º Ano', '5º Ano', '9º Ano', '3ª Série EM']
anos = [ano for ano in range(2012, 2024) if ano not in [2020, 2021]]  # Anos de 2012 a 2023, exceto 2020 e 2021
componentes = ['LÍNGUA PORTUGUESA', 'MATEMÁTICA']
credes = ['FORTALEZA', 'MARACANAU', 'ITAPIPOCA', 'ACARAU', 'CAMOCIM', 'TIANGUA', 'SOBRAL', 'CANINDE',
          'BATURITE', 'HORIZONTE', 'RUSSAS', 'JAGUARIBE', 'QUIXADA', 'CRATEUS', 'SENADOR POMPEU',
          'TAUA', 'IGUATU', 'ICO', 'CRATO', 'JUAZEIRO DO NORTE', 'BREJO SANTO']
regioes_planejamento_list = list(regioes_planejamento.keys())

# Seletores
col1, col2 = st.columns(2)
with col1:
    etapa = st.selectbox("ETAPA:", etapas)
    ano = st.selectbox("ANO:", anos)
    componente = st.selectbox("COMPONENTE CURRICULAR:", componentes)
with col2:
    mapa_tipo = st.selectbox("Selecione o tipo de mapa:", ["CREDE", "REGIÃO DE PLANEJAMENTO", "CEARÁ"])
    if mapa_tipo == "CREDE":
        crede = st.selectbox("CREDE:", credes)
    elif mapa_tipo == "REGIÃO DE PLANEJAMENTO":
        crede = st.selectbox("REGIÃO DE PLANEJAMENTO:", regioes_planejamento_list)
    else:
        crede = None

# Estado para controlar a exibição dos nomes dos municípios
if 'mostrar_nomes' not in st.session_state:
    st.session_state.mostrar_nomes = True

# Caixa de seleção para mostrar/ocultar nomes dos municípios
texto_checkbox = "Mostrar nomes dos Municípios" if st.session_state.mostrar_nomes else "Não mostrar nomes dos Municípios"
st.session_state.mostrar_nomes = st.checkbox(texto_checkbox, value=st.session_state.mostrar_nomes)

# Botão para gerar o mapa
if st.button("Gerar Mapa"):
    fig = generate_map(etapa, ano, componente, crede, mapa_tipo, st.session_state.mostrar_nomes)
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

# Rodapé com copyright
st.markdown(
    """
    <div style="text-align: center; margin-top: 50px; font-size: 12px; color: #666;">
        © 2023 Gerador de Mapas SPAECE. Setor de Processamento e Monitoramento de Resultados - SPMR-DAM/SME Maracanaú. <br>Todos os direitos reservados.
    </div>
    """,
    unsafe_allow_html=True
)
