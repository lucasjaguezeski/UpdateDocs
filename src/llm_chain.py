# Standard libraries
import logging
import json
import os

# Carrega as variáveis de ambiente do arquivo .env
from dotenv import load_dotenv
load_dotenv()

# LangChain libraries
from langchain_google_genai import GoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.messages import HumanMessage, AIMessage

# Configuração do log de erros
log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs", "errors.log")
os.makedirs(os.path.dirname(log_path), exist_ok=True)
logging.basicConfig(
    filename=log_path,
    level=logging.ERROR,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def enumerate_lines(documentation):
    """
    Enumera as linhas de um texto de documentação.
    Retorna uma string com as linhas numeradas.
    """
    # Divide o texto de documentação em linhas
    lines = documentation.splitlines()

    # Enumera as linhas e as concatena
    enumerated_documentation = "".join(f"{i+1}: {line}" for i, line in enumerate(lines))

    # Verifica se não houve algum erro
    if not enumerated_documentation:
        logging.error("Erro ao enumerar as linhas do texto de documentação.")
        return None
    
    return enumerated_documentation

def create_model():
    """
    Inicializa o modelo de IA.
    Retorna o modelo inicializado ou None em caso de erro.
    """
    try:
        model = GoogleGenerativeAI(
            model="gemini-2.0-flash-exp",
            temperature=1
        )
        return model
    except Exception as e:
        logging.error(f"Erro ao inicializar o modelo: {e}")
        return None

def get_system_prompt():
    system_prompt = """
        Você é um assistente especializado em gerar documentação de software.
        Receba o diff do commit e o conteúdo atual da documentação e atualize ou adicione
        linhas que reflitam as alterações feitas no commit.

        Instrução:
        Para cada alteração identificada, faça o seguinte:
        1. Determine a linha inicial e a linha final (usando a contagem a partir de 1) no conteúdo atual da documentação onde a alteração deve ser aplicada.
        2. Gere o novo conteúdo que deverá substituir o trecho identificado ou ser inserido nesse local. **O novo conteúdo DEVE estar formatado em Markdown**, utilizando as convenções do Markdown (como cabeçalhos, listas, ênfases, etc.), conforme necessário.

        Sua resposta DEVE ser um JSON válido, sem nenhum comentário ou explicação adicional, no seguinte formato:

        {{
        "alteracoes": [
            {{
            "inicio": 17,
            "fim": 19,
            "novo_conteudo": "# Guia de Instalação  \nExecute o comando abaixo para configurar o ambiente:  \nbash install.sh \nCaso encontre problemas, consulte a seção de **Solução de Problemas**."
            }},
            ... // outras alterações, se houver
        ]
        }}

        Certifique-se de:
        - Utilizar apenas números inteiros para "inicio" e "fim".
        - Incluir apenas o JSON na resposta, sem textos extras.
        - Mantenha o estilo da documentação atual, incluindo cabeçalhos, listas, ênfases, etc.
    """
    return system_prompt

def create_chain(commit_diff, documentation_content):
    # Inicialização do modelo
    model = create_model()

    if not model:
        logging.error("Erro ao criar a cadeia de execução.")
        return None

    # Inicialização do template de conversa
    prompt = ChatPromptTemplate.from_messages([
        ("system", get_system_prompt()),
        ("human", "Diff do commit:\n{commit_diff}\n\nDocumentação existente:\n{documentation_content}\n\nObs.: As linhas estão numeradas para referência, mas não devem ser parte da resposta.")
    ])

    # Inicialização do parser
    parser = JsonOutputParser()

    # Inicialização da cadeia de execução
    chain = (
        prompt
        | model
        | parser
    )

    return chain

def run_chain(chain, commit_diff, documentation_content):
    # Verificação básica de tamanho
    if len(commit_diff) > 100000 or len(documentation_content) > 100000:
        logging.error("Entrada muito grande para processamento seguro.")
        return None
    
    # Executa a cadeia de execução
    try:
        response = chain.invoke({"commit_diff": commit_diff, "documentation_content": documentation_content})
    except Exception as e:
        logging.error(f"Erro ao executar a cadeia de execução: {e}")
        return None
    return response

def generate_documentation_changes(commit_diff, documentation_content):
    # Enumera as linhas do texto de documentação para referência
    documentation_content = enumerate_lines(documentation_content)

    # Cria a cadeia de execução
    chain = create_chain(commit_diff, documentation_content)

    # Executa a cadeia de execução
    response = run_chain(chain, commit_diff, documentation_content)
    
    # Verifica se não houve algum erro
    if not response:
        logging.error("Erro ao executar a cadeia de execução.")
        return None

    return json.dumps(response, ensure_ascii=False)
