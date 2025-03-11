# UpdateDocs

O UpdateDocs tem como objetivo automatizar a documentação de projetos utilizando inteligência artificial. A cada commit, o script [UpdateDocs.py](c:/Users/lucas/Desktop/UpdateDocs/UpdateDocs.py) atualiza a documentação do projeto, considerando as alterações realizadas no código-fonte.

---

## Sobre o Script

O script [UpdateDocs.py](c:/Users/lucas/Desktop/UpdateDocs/UpdateDocs.py) realiza as seguintes operações:

- **Validação**: Verifica o diretório do repositório e a validade do hash do commit.
- **Diff e Arquivos Editados**: Obtém a lista de arquivos alterados e o diff específico de cada um.
- **Mapeamento entre Código e Documentação**: Gera o caminho dos arquivos de documentação correspondentes aos arquivos de código-fonte (por exemplo, substituindo a pasta `src` por `docs` e a extensão `.py` por `.md`).
- **Atualização de Documentação**: Lê o conteúdo atual dos arquivos de documentação e utiliza uma LLM (por meio da biblioteca LangChain) para gerar atualizações em Markdown.
- **Aplicação das Alterações**: Atualiza os arquivos de documentação com o novo conteúdo sugerido.

---

## Como Utilizar?

### 1. Configure o seu post-commit

Siga os passos abaixo para adicionar o script ao hook `post-commit` no Git:

1. **Abra o terminal.**
2. **Navegue até o diretório do seu repositório Git:**
    ```sh
    cd /caminho/para/seu/repositorio
    ```
3. **Crie o diretório de hooks (caso não exista):**
    ```sh
    mkdir -p .git/hooks
    ```
4. **Edite o arquivo `post-commit`:**
    ```sh
    nano .git/hooks/post-commit
    ```
5. **Adicione o seguinte conteúdo:**
    ```sh
    #!/bin/bash

    # Ir para o diretório raiz do repositório
    REPO_DIR=$(git rev-parse --show-toplevel) || exit

    # Capturar o hash do commit mais recente
    COMMIT_HASH=$(git rev-parse HEAD)

    # Ir para o diretório onde está o UpdateDocs
    cd ~/caminho/para/UpdateDocs || exit

    # Executar o script Python com o caminho do repositório e o hash do commit
    python src/UpdateDocs.py "$REPO_DIR" "$COMMIT_HASH" >> logs/errors.log 2>&1

    # Se estiver usando um ambiente virtual:
    #~/caminho/para/UpdateDocs/venv/bin/python src/UpdateDocs.py "$REPO_DIR" "$COMMIT_HASH" >> logs/error.log 2>&1

    ```
6. **Salve o arquivo e saia do editor** (no Nano: `Ctrl + O` para salvar e `Ctrl + X` para sair).
7. **Torne o arquivo executável:**
    ```sh
    chmod +x .git/hooks/post-commit
    ```

### 2. Configure a sua API do Gemini Gratuitamente

#### Passo 1: Gerar a Chave API

1. Acesse o site do Gemini: [Gemini API Documentation](https://ai.google.dev/gemini-api/docs?hl=pt-br).
2. Siga as instruções para criar sua conta e gerar uma chave API.
3. Copie a chave gerada e mantenha-a em local seguro.

#### Passo 2: Configurar a Variável de Ambiente

1. **Abra o terminal.**
2. **Adicione a chave API como variável de ambiente `GOOGLE_API_KEY`:**

   **No Linux ou macOS:**
   - Edite seu arquivo de configuração (por exemplo, `~/.bashrc`):
     ```sh
     nano ~/.bashrc
     ```
   - Adicione a linha:
     ```sh
     export GOOGLE_API_KEY="sua-chave-api-aqui"
     ```
   - Salve e feche o editor, depois execute:
     ```sh
     source ~/.bashrc
     ```

   **No Windows:**
   - Abra o Prompt de Comando como administrador e execute:
     ```cmd
     setx GOOGLE_API_KEY "sua-chave-api-aqui"
     ```
   - Feche e abra novamente o Prompt de Comando para que as alterações tenham efeito.

  ### **Importante:**
   Se você estiver usando um ambiente virtual, a variável GOOGLE_API_KEY deve estar configurada e acessível neste ambiente.

---

## Estrutura de Pastas

Para que o código funcione corretamente, os arquivos de documentação devem ter a mesma estrutura dos arquivos de código-fonte, alterando apenas a pasta e a extensão dos arquivos. Veja um exemplo:

```plaintext
meu_projeto/
├── src/
│   ├── Main.java
│   ├── utils/
│   │   └── Helper.py
│   └── components/
│       └── Button.js
└── docs/
    ├── Main.md
    ├── utils/
    │   └── Helper.md
    └── components/
        └── Button.md
````

**Nota:** Certifique-se de que a estrutura de diretórios e os nomes dos arquivos estejam corretos para garantir que o caminho do arquivo de documentação seja gerado corretamente.

---

## Lista de Dependências
### Backend
- **Python 3.x** (versão 3.7 ou superior recomendada)
- **FastAPI** – para a criação do endpoint REST
- **uvicorn** – para executar o servidor ASGI do FastAPI
- **pydantic** – para validação dos dados (já vem como dependência do FastAPI)
- **langchain_google_genai** – utilizado para interagir com o Google Generative AI
- **langchain** – para manipulação de prompts e execução de LLMs
- **langchain_core** – para os output parsers e runnables

### Frontend
- **Node.js** – runtime necessário para executar o ambiente Node e o NPM (versão LTS recomendada)
- **npm ou yarn** – gerenciador de pacotes
- **react** – biblioteca principal para construção da interface
- **react-dom** – para renderização dos componentes no DOM
- **react-scripts** – se estiver utilizando Create React App ou estrutura similar
- **react-markdown** – para renderização de Markdown
- **remark-gfm** – para suporte ao GitHub Flavored Markdown
- **react-syntax-highlighter** – para realce de sintaxe dos blocos de código
- **prismjs** – (por trás do react-syntax-highlighter) para estilos (por exemplo, com o tema `vscDarkPlus`)

## Considerações Finais

Após configurar o `post-commit` e a chave api, o arquivo `UpdateDocs.py` será acionado automaticamente a cada commit, mantendo a documentação do seu projeto sempre atualizada com base nas alterações do código-fonte.

Sinta-se à vontade para contribuir e sugerir melhorias para este projeto! 🚀🚀🚀