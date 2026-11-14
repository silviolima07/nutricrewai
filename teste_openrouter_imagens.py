
from pathlib import Path

from app.config import Settings
from app.services.providers.openrouter_provider import OpenRouterProvider


PROMPT = """
Analise a imagem e identifique somente alimentos visíveis.

Para cada alimento, informe:
- Nome do alimento
- Confiança: alta, média ou baixa
- Justificativa breve da identificação

Não invente ingredientes ou alimentos.

Se não houver alimentos na imagem, responda
exatamente: Nenhum alimento identificado.

Responda em português.
"""


def testar_imagem(provedor, caminho):
    print(f"\nTestando: {caminho}")

    imagem = Path(caminho).read_bytes()

    resultado = provedor.descrever(
        imagem=imagem,
        mime_type="image/png",
        prompt=PROMPT
    )

    print("Provedor:", resultado.provedor)
    print("Resposta:\n", resultado.descricao)


def main():
    config = Settings()

    openrouter = OpenRouterProvider(
        api_key=config.openrouter_api_key,
        model=config.openrouter_vision_model
    )

    # Teste 1: prato com alimentos
    testar_imagem(openrouter, "img/prato.png")

    # Teste 2: imagem de utensílios
    testar_imagem(openrouter, "img/garfo_e_colher.png")


if __name__ == "__main__":
    main()
