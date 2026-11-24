import hashlib
import os
from pathlib import Path

from dotenv import load_dotenv
import requests
import streamlit as st


load_dotenv()
IMAGENS = Path(__file__).resolve().parent / "img"
API_URL = os.getenv("NUTRICREW_API_URL", "http://127.0.0.1:8000").rstrip("/")
MAX_BYTES = 5 * 1024 * 1024


def solicitar_analise(nome, dados, mime_type, observacoes):
    try:
        resposta = requests.post(
            f"{API_URL}/api/v1/analisar",
            files={"imagem": (nome, dados, mime_type)},
            data={"observacoes": observacoes},
            timeout=(5, 120),
        )
    except requests.Timeout:
        st.error("A API demorou a responder. Tente novamente mais tarde.")
        return None
    except requests.RequestException:
        st.error("Não foi possível acessar a API. Confira se o Uvicorn está rodando.")
        return None

    try:
        resultado = resposta.json()
    except ValueError:
        st.error("A API retornou uma resposta que não pôde ser lida.")
        return None

    if not resposta.ok:
        detalhe = resultado.get("detail") if isinstance(resultado, dict) else None
        st.error(detalhe if isinstance(detalhe, str) else f"Falha na análise (HTTP {resposta.status_code}).")
        return None

    if (
        not isinstance(resultado, dict)
        or not isinstance(resultado.get("descricao"), str)
        or resultado.get("status") not in ("analisado", "sem_alimentos")
        or (
            resultado["status"] == "analisado"
            and not isinstance(resultado.get("relatorio"), str)
        )
    ):
        st.error("A API retornou um resultado em formato inesperado.")
        return None

    return resultado


st.title("Avalie sua alimentação")
st.sidebar.image(str(IMAGENS / "garfo_e_colher.png"))
option = st.sidebar.selectbox("Menu", ["Carregar imagem", "Sobre"])

if option == "Carregar imagem":
    observacoes = st.sidebar.multiselect(
        "Observações e objetivos",
        [
            "Intolerância à lactose", "Alergia a amendoim", "Emagrecer",
            "Manter o peso", "Ganhar massa muscular", "Diabetes",
            "Não consome carne vermelha", "Sedentário", "Obeso",
        ],
        default=["Manter o peso"],
    )
    arquivo = st.file_uploader("Envie uma foto JPEG ou PNG", type=["jpg", "jpeg", "png"])
    if arquivo is None:
        st.session_state.pop("analise_refeicao", None)
    elif arquivo.size > MAX_BYTES:
        st.session_state.pop("analise_refeicao", None)
        st.error("A imagem deve ter no máximo 5 MiB.")
    else:
        dados = arquivo.getvalue()
        selecao = (hashlib.sha256(dados).digest(), tuple(observacoes))
        if st.session_state.get("analise_refeicao", (None,))[0] != selecao:
            st.session_state.pop("analise_refeicao", None)

        try:
            st.image(dados, caption=arquivo.name)
        except (OSError, ValueError):
            st.error("Não foi possível abrir a imagem.")
            st.stop()

        if st.button("Analisar refeição"):
            st.session_state.pop("analise_refeicao", None)
            with st.spinner("Analisando a foto e preparando o relatório…"):
                resultado = solicitar_analise(arquivo.name, dados, arquivo.type, observacoes)
            if resultado is not None:
                st.session_state["analise_refeicao"] = (selecao, resultado)

        if "analise_refeicao" in st.session_state:
            _, resultado = st.session_state["analise_refeicao"]
            if resultado["status"] == "sem_alimentos":
                st.info(resultado["descricao"])
            else:
                st.subheader("Alimentos identificados")
                st.text(resultado["descricao"])
                st.subheader("Relatório nutricional")
                st.markdown(resultado["relatorio"])
                st.download_button(
                    "Baixar análise",
                    data=resultado["relatorio"],
                    file_name="analise.md",
                    mime="text/markdown",
                )

if option == "Sobre":
    st.markdown(
        "A visão descreve os alimentos visíveis na foto. Quando encontra alimentos, "
        "o serviço nutricional gera um relatório considerando suas observações."
    )
    st.subheader("Exemplo")
    st.image(str(IMAGENS / "prato.png"))
    st.subheader("Resultado da análise")
    st.write("""
Arroz: não há informações explicitas sobre os nutrientes contidos na descrição, mas como o arroz tem sua classificação em diferentes tipos como, arroz branco e arroz integral, ele contém carboidratos no calórico de 130 e fibras como o RIAI. O benefício para a saúde é que ajuda a controlar o nível de açúcar no sangue e a regular o trânsito intestinal. Alternativa mais saudável: no caso de que você optar pelo arroz integral, pois possui 100 calorias e 2gr de fibras por 100gr.

Vegetais (legumes e verduras): como a descrição, não haver informações sobre os vegetais contidos, os vegetais contém vitaminas, minerais e fibras. Cada xícara de vegetais cozidos fornece cerca de 50 calorias. Mas como na descrição indica, quando se faza desta forma, não se podem dizer qual tipo de vegetal os inclua, mas qual seja ficou para ele ser definido por um especialista. Mas, É provável que os vegetais incluídos sejam ricos em vitamina C, vitamina A, potássio e fibras. O benefício para a saúde é que ajudam a prevenir doenças crônicas, como câncer e doenças cardíacas, e a regular o trânsito intestinal. Alternativa mais saudável: no caso de que você optar pelos vegetais mais probamos saudáveis e menos calórias, pois os vegetais diminuíram as calorias. Porém, como não sabe qual os vegetais inclui a descrição, é difícil identificar qual tipo de vegetal.

Já os alimentos que podem ser considerados menos saudáveis ou que devem ser consumidos em moderação são:

Carne (meat): como a descrição não indica qual tipo de carne, não se sabe quais nutrientes contém, mas é importante notar que a carne vermelha consumida em excesso pode contribuir para o aumento do risco de doenças cardíacas e câncer. Além disso, a gordura presente na carne pode ser alta em calorias e gorduras saturadas. Cada 100g de carne fornece cerca de 250 calorias. O benefício para a saúde é que fornece proteínas essenciais para o crescimento e desenvolvimento. Alternativa mais saudável: optar por cortes de carne mais magros ou por fontes de proteínas mais saudáveis, como peixe ou frango.

Um resumo final:

Relembrando, a avaliação acima pode variar dependendo do tipo de vegetal. Em definitivo, verificado isso faz com que os alimentos possam ou não ser saudáveis.
    .""")
