
from groq import Groq, APIConnectionError, APITimeoutError, RateLimitError, InternalServerError

from app.services.vision_provider import VisionResult
from app.services.vision_service import RecoverableVisionError


class GroqProvider:

    def __init__(self, api_key: str, model: str):
        self.client = Groq(api_key=api_key)
        self.model = model

    def descrever(
        self,
        imagem: bytes,
        mime_type: str,
        prompt: str
    ) -> VisionResult:

        import base64

        imagem_base64 = base64.b64encode(imagem).decode("utf-8")

        try:
            resposta = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": (
                                        f"data:{mime_type};base64,"
                                        f"{imagem_base64}"
                                    )
                                }
                            }
                        ]
                    }
                ],
                temperature=0.2,
                max_tokens=700
            )

            descricao = resposta.choices[0].message.content

            return VisionResult(
                descricao=descricao,
                provedor="groq"
            )

        except (
            APIConnectionError,
            APITimeoutError,
            RateLimitError,
            InternalServerError
        ) as erro:
            raise RecoverableVisionError(
                "Falha temporária no Groq"
            ) from erro
