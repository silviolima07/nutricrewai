
from app.services.providers.openrouter_provider import (
    OpenRouterProvider
)


def test_openrouter_descreve_imagem(requests_mock):

    # Simula uma resposta da API
    requests_mock.post(
        OpenRouterProvider.URL,
        json={
            "choices": [
                {
                    "message": {
                        "content": "Arroz, feijão e frango"
                    }
                }
            ]
        },
        status_code=200
    )

    # Cria o provedor
    provedor = OpenRouterProvider(
        api_key="chave-falsa",
        model="modelo-teste"
    )

    # Executa o método
    resultado = provedor.descrever(
        imagem=b"imagem-simulada",
        mime_type="image/jpeg",
        prompt="Descreva os alimentos"
    )

    # Verifica o resultado
    assert resultado.descricao == "Arroz, feijão e frango"
    assert resultado.provedor == "openrouter"
