
import base64
import requests

from app.services.vision_provider import VisionResult
from app.services.vision_service import RecoverableVisionError


class OpenRouterProvider:

    URL = "https://openrouter.ai/api/v1/chat/completions"

    def __init__(self, api_key: str, model: str):
        self.api_key = api_key
        self.model = model

    def descrever(
        self,
        imagem: bytes,
        mime_type: str,
        prompt: str
    ) -> VisionResult:

        imagem_b64 = base64.b64encode(imagem).decode("utf-8")

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": (
                                    f"data:{mime_type};base64,"
                                    f"{imagem_b64}"
                                )
                            }
                        }
                    ]
                }
            ],
            "temperature": 0.2,
            "max_tokens": 4096
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        try:
            resposta = requests.post(
                self.URL,
                json=payload,
                headers=headers,
                timeout=30
            )

            if resposta.status_code == 429 or (
                500 <= resposta.status_code < 600
            ):
                raise RecoverableVisionError(
                    "OpenRouter temporariamente indisponível"
                )

            resposta.raise_for_status()

            dados = resposta.json()
            escolha = dados["choices"][0]
            mensagem = escolha["message"]

            descricao = mensagem.get("content")

            print("Modelo utilizado:", dados.get("model"))
            print("Motivo do encerramento:", escolha.get("finish_reason"))
            print("Conteúdo vazio:", not bool(descricao))

            if not isinstance(descricao, str) or not descricao.strip():
                raise ValueError(
                    "OpenRouter não retornou uma descrição textual"
                )


            return VisionResult(
                descricao=descricao,
                provedor="openrouter"
            )

        except (requests.Timeout, requests.ConnectionError) as erro:
            raise RecoverableVisionError(
                "Falha de conexão com OpenRouter"
            ) from erro
