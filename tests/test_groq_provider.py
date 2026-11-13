
from types import SimpleNamespace

from app.services.providers import groq_provider


def test_groq_descreve_imagem(monkeypatch):

    class GroqSimulado:
        def __init__(self, api_key):
            self.chat = SimpleNamespace(
                completions=SimpleNamespace(
                    create=self.criar_resposta
                )
            )

        def criar_resposta(self, **kwargs):
            assert kwargs["model"] == "modelo-teste"

            conteudo = kwargs["messages"][0]["content"]
            imagem_url = conteudo[1]["image_url"]["url"]

            assert imagem_url.startswith(
                "data:image/jpeg;base64,"
            )

            return SimpleNamespace(
                choices=[
                    SimpleNamespace(
                        message=SimpleNamespace(
                            content="Arroz, feijão e frango"
                        )
                    )
                ]
            )

    monkeypatch.setattr(
        groq_provider,
        "Groq",
        GroqSimulado
    )

    provedor = groq_provider.GroqProvider(
        api_key="chave-falsa",
        model="modelo-teste"
    )

    resultado = provedor.descrever(
        imagem=b"imagem-simulada",
        mime_type="image/jpeg",
        prompt="Descreva os alimentos"
    )

    assert resultado.descricao == "Arroz, feijão e frango"
    assert resultado.provedor == "groq"
