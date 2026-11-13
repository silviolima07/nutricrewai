
from pathlib import Path

from app.config import Settings
from app.services.vision_service import VisionService
from app.services.providers.groq_provider import GroqProvider
from app.services.providers.openrouter_provider import OpenRouterProvider


def main():
    # 1. Carregar configuracoes
    config = Settings()

    # 2. Criar os provedores
    groq = GroqProvider(
        api_key=config.groq_api_key,
        model=config.groq_vision_model
    )

    openrouter = OpenRouterProvider(
        api_key=config.openrouter_api_key,
        model=config.openrouter_vision_model
    )

    # 3. Injetar os provedores no servico
    servico = VisionService(
        principal=groq,
        secundario=openrouter
    )

    # 4. Carregar imagem diretamente em memoria
    imagem = Path("img/prato.png").read_bytes()

    prompt = (
        "Descreva em portugues apenas os alimentos "
        "visiveis nesta imagem. "
        "Nao invente alimentos que nao consegue identificar. "
        "Se nao houver alimentos, responda: Nenhum alimento."
    )

    # 5. Executar a analise
    resultado = servico.descrever(
        imagem=imagem,
        mime_type="image/png",
        prompt=prompt
    )

    # 6. Exibir resultado
    print("\nProvedor utilizado:", resultado.provedor)
    print("Descricao:", resultado.descricao)


if __name__ == "__main__":
    main()
