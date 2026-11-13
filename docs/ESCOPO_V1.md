# NutriCrewAI — Escopo e critérios de aceite da v1.0

**Status:** Escopo definido, antes da implementação  
**Data:** 13/11/2026  
**Repositório:** https://github.com/silviolima07/nutricrewai

## 1. Objetivo

Evoluir a aplicação atual de análise de refeições por fotografia para uma arquitetura **modular e API-first**, preservando seu comportamento principal: receber uma imagem e observações do usuário, identificar os alimentos e oferecer uma análise nutricional **informativa**.

O produto final desta versão deverá permitir trocar a interface (por exemplo, Streamlit por mobile ou React) sem reescrever o processamento.

## 2. Estado inicial do projeto

Código importado de `agente_nutri`:
- `app.py`: interface Streamlit e fluxo principal;
- `utils.py`: codificação e descrição de imagens via Groq e chamada à Crew;
- `crew_nutri.py`: um agente nutricionista CrewAI, uma tarefa, sem ferramentas registradas (`tools=[]`);
- `MyLLM.py`: configurações de modelos, a revisar;
- `pyproject.toml`: dependências atuais.

**Observação técnica:** o componente de visão é uma chamada a um modelo multimodal Groq, **não** um segundo agente CrewAI. O sistema contém um agente CrewAI nutricional.

**Problema identificado:** o `app.py` salva uploads no caminho fixo `image.png`, criando risco de sobrescrita entre requisições simultâneas.

## 3. Funcionalidades obrigatórias

1. Interface Streamlit para enviar imagem e selecionar objetivos/restrições.
2. Endpoint FastAPI `POST /api/v1/analisar` para receber imagem e observações e devolver JSON.
3. Validação de arquivo (tipo, tamanho e imagem decodificável), com erros claros.
4. Descrição dos alimentos por modelo multimodal acessado via Groq.
5. Orquestração por LangGraph, com estado por execução e roteamento condicional.
6. Se não houver alimento identificável, retornar mensagem apropriada sem chamar a Crew.
7. Se houver alimento, invocar a análise nutricional por CrewAI, considerando as observações informadas.
8. Exibir resultado no Streamlit e permitir baixá-lo.
9. Tratar falhas de API, timeouts e limites de serviço sem misturar resultados.
10. Documentar configuração, variáveis de ambiente, execução e testes.

## 4. Arquitetura funcional

```text
Streamlit (imagem + observações)
          |
          v
FastAPI — POST /api/v1/analisar
          |
          v
LangGraph (estado exclusivo por execução)
          |
          v
Nó: descrever_imagem  --->  serviço de visão (Groq)
          |
          v
Decisão: há alimentos?
        /          \
       não         sim
       |            |
       v            v
Nó: sem_alimentos  Nó: analisar_nutricao ---> serviço CrewAI
       |            |
       +------+-----+
              |
              v
       Resposta JSON
              |
              v
          Streamlit
```

**Separação de responsabilidades:**
- **FastAPI** recebe/valida requisições e formata respostas, sem implementar a lógica nutricional.
- **LangGraph** controla os nós, o estado e a condição de roteamento; não deve conter chamadas Groq/CrewAI acopladas às rotas.
- **Serviço de visão** recebe bytes e devolve descrição estruturada ou indicação de ausência de alimento.
- **Serviço de nutrição** encapsula o CrewAI e recebe descrição + observações.
- **Streamlit** é cliente HTTP da API; não executa diretamente serviços de IA.

## 5. Contrato inicial de API

**Requisição:** `POST /api/v1/analisar`, `multipart/form-data`
- `imagem`: JPG ou PNG (limite inicial proposto: 5 MB);
- `observacoes`: lista de objetivos/restrições, conforme contrato a implementar.

**Resposta JSON conceitual:**
```json
{
  "status": "analisado",
  "descricao": "Arroz, feijão e frango no prato.",
  "relatorio": "Avaliação nutricional informativa..."
}
```

Para imagem sem alimentos: `status: "sem_alimentos"` e mensagem clara; `relatorio: null`. Respostas de erro deverão ter códigos HTTP e mensagens consistentes. O contrato exato será versionado e testado antes de integrar a interface.

## 6. Segurança, concorrência e limites

- Não persistir uploads em arquivo compartilhado (`image.png`); processar bytes em memória e descartar após o uso.
- Não manter estado mutável de imagem, observações ou resultado em variáveis globais compartilhadas.
- Cada execução do LangGraph terá seu próprio estado; atenção a qualquer objeto de serviço compartilhado que não seja seguro para concorrência.
- Validar tamanho, tipo e decodificação da imagem; não confiar apenas na extensão.
- Manter chaves de API em variáveis de ambiente, fora do Git; usar `.env.example` sem segredos.
- Definir timeout, tratamento de falhas e limite simples de chamadas concorrentes para evitar saturação/cotas da Groq.
- Testar requisições simultâneas com serviços simulados para confirmar isolamento entre usuários.
- Não apresentar como precisos calorias, porções ou ausência de alérgenos deduzidos apenas de fotografias.

## 7. Fora do escopo da v1.0

- Cadastro, login ou perfis persistentes;
- banco de dados e histórico de refeições;
- aplicativo mobile nativo ou frontend React;
- múltiplos agentes CrewAI adicionais, novas ferramentas externas ou RAG;
- contagem precisa de calorias e diagnóstico/recomendação médica individualizada;
- filas distribuídas, Redis, Celery e implantação escalável complexa.

Pedidos novos devem ir para backlog futuro, sem interromper a v1.0.

## 8. Plano incremental e critérios por etapa

| Etapa | Entrega | Critério de pronto |
| --- | --- | --- |
| 1. Modularização | Separar visão, nutrição e interface | Serviços executam sem importar Streamlit; testes unitários básicos |
| 2. LangGraph | Estado, nós e roteamento condicional | Rotas com/sem alimentos cobertas por testes |
| 3. FastAPI | Endpoint de análise, validações e JSON | Testes de API e erros esperados |
| 4. Streamlit | Consumo HTTP da API | Envio e resultado pela interface sem chamada direta a Groq/CrewAI |
| 5. Qualidade | Concorrência, timeouts, documentação | Testes de isolamento e instruções de execução reproduzíveis |

**Regra de trabalho:** cada módulo deve ter responsabilidade, entradas, saídas, teste e critério de pronto. Integrar somente após sua validação.

## 9. Critérios finais de aceite da v1.0

- [ ] Uma fotografia enviada pelo Streamlit chega à API e é analisada por Groq → LangGraph → CrewAI.
- [ ] Objetivos/restrições informados aparecem de forma consistente no relatório.
- [ ] Imagens sem alimentos são tratadas sem executar análise nutricional.
- [ ] Arquivos inválidos/grandes e falhas externas resultam em mensagens controladas.
- [ ] Requisições simultâneas não misturam imagens, observações ou relatórios.
- [ ] O relatório é exibido e pode ser baixado.
- [ ] As dependências, configurações e instruções de execução estão no README.
- [ ] Os testes relevantes passam com serviços simulados; ao menos um teste de ponta a ponta é documentado.

## 10. Decisões de arquitetura

- **API-first** para permitir múltiplos clientes no futuro.
- **LangGraph** como roteador/orquestrador, mantendo serviços independentes do framework.
- **CrewAI** preservado para avaliação nutricional, sem introduzir agentes extras.
- **MVP pequeno, sem persistência**, com segurança de concorrência por execução.
- Trabalho em branch de feature, preservando a versão importada na `main`.

> Este documento descreve o escopo aprovado para implementação, não funcionalidades já concluídas. Mudanças de escopo devem ser registradas explicitamente.
