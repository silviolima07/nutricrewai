# nutricrewai
Projeto usando CrewAI.

## API de análise

Use Python 3.12 e preencha as credenciais e os modelos no arquivo local
`.env`, com base em `.env.example`. O modelo de nutrição usa
`GROQ_NUTRITION_MODEL`, com o modelo de visão como padrão quando o campo
está vazio.

```sh
uv sync --locked --python 3.12
uv run --locked python -m uvicorn app.api:app
```

Abra [a documentação interativa](http://127.0.0.1:8000/docs) para testar
`POST /api/v1/analisar`. Envie o arquivo no campo `imagem` e, se houver,
repita o campo `observacoes` para cada objetivo ou restrição. O endpoint
aceita JPEG e PNG de até 5 MiB e 25 megapixels. A resposta contém
`status`, `descricao` e `relatorio`.

Os testes da API exercitam o endpoint com um executor simulado. Execute
`uv run --locked python -m pytest` na raiz do projeto.
