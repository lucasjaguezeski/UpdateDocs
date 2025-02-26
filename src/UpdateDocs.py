import sys
import os
import json
import subprocess
from langchain_google_genai import GoogleGenerativeAI
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from request import server_init, approve_changes
from interface_controller import ReactManager
import logging

logging.basicConfig(
    filename=r'logs\errors.log',
    level=logging.ERROR,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def get_cfg():
    """
    Obtém as configurações do arquivo de configuração.
    """
    # Configuração inicial
    repo_path = sys.argv[1]
    commit_hash = sys.argv[2]

    # Verifica se o diretório do repositório existe
    if not os.path.isdir(repo_path):
        logging.error(f"Diretório do repositório não encontrado: {repo_path}")
        raise ValueError(f"Diretório do repositório não encontrado: {repo_path}")
    
    # Verifica se o hash do commit é válido
    try:
        subprocess.run(
            ["git", "cat-file", "-t", commit_hash],
            check=True,
            cwd=repo_path  # Usa o diretório do repositório especificado
        )
    except subprocess.CalledProcessError as e:
        logging.error(f"Hash do commit inválido: {commit_hash}")
        raise ValueError(f"Hash do commit inválido: {commit_hash}")

    return repo_path, commit_hash

def save_documentation_changes(file_path, updated_lines):
    try:
        with open(file_path, "w", encoding="utf-8") as file:
            file.writelines(updated_lines)
    except Exception as e:
        logging.error(f"Erro ao salvar as alterações no arquivo: {e}")
        raise ValueError(f"Erro ao salvar as alterações no arquivo: {e}")
    
def get_file_diff(repo_path, commit_hash, file_path):
    """
    Obtém o diff de um arquivo específico no commit.
    """
    try:
        # Usa -- para informar qual arquivo filtrar
        result = subprocess.run(
            ["git", "show", commit_hash, "--", file_path],
            capture_output=True,
            text=True,
            check=True,
            cwd=repo_path
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        logging.error(f"Erro ao obter o diff do arquivo {file_path}: {e.stderr}")
        raise ValueError(f"Erro ao obter o diff do arquivo {file_path}: {e.stderr.strip()}")
    
def get_edited_files(repo_path, commit_hash):
    """
    Obtém uma lista de arquivos editados em um commit específico usando o Git.
    Retorna uma lista de nomes de arquivos.
    """
    try:
        result = subprocess.run(
            ["git", "diff-tree", "--no-commit-id", "--name-only", "-r", commit_hash],
            capture_output=True,
            text=True,
            check=True,
            cwd=repo_path  # Usa o diretório do repositório especificado
        )
        return result.stdout.splitlines()
    except subprocess.CalledProcessError as e:
        logging.error(f"Erro ao obter os arquivos editados: {e.stderr}")
        raise ValueError(f"Erro ao obter os arquivos editados: {e.stderr.strip()}")
    
def get_doc_path(repo_path, src_file):
    """
    Gera e retorna o caminho do arquivo de documentação (.md) correspondente a um arquivo de código-fonte.
    Verifica se o arquivo de entrada possui uma das extensões permitidas (".java", ".py", ".js", ".ts")
    e se contém a palavra "src" em seu caminho. Caso essas condições sejam atendidas, substitui a extensão
    origem por ".md" e a pasta "src" por "docs", concatenando com o caminho do repositório fornecido. Se não
    for possível aplicar a transformação, retorna None.
    Parâmetros:
        repo_path (str): Caminho do repositório onde se encontram os arquivos.
        src_file (str): Caminho relativo do arquivo de código-fonte.
    Retorna:
        str ou None: Caminho completo do arquivo de documentação se o arquivo for compatível; caso contrário, None.
    """
    src_extensions = [".java", ".py", ".js", ".ts"] # Pode ser expandido para outras extensões de código-fonte

    if any(src_file.endswith(ext) for ext in src_extensions) and "src" in src_file:
        for ext in src_extensions:
            if src_file.endswith(ext):
                doc_file_name = src_file.replace(ext, ".md").replace("src", "docs")
                break
        doc_file = (f'{repo_path}/{doc_file_name}')
        return doc_file
    else:
        return None

def get_documentation_content(doc_path):
    """
    Lê e concatena o conteúdo de uma lista de arquivos de documentação.
    Retorna uma string com o conteúdo dos arquivos selecionados.
    """
    if os.path.isfile(doc_path):
        try:
            with open(doc_path, "r", encoding="utf-8") as doc_file:
                lines = doc_file.readlines()
                documentation = "".join(lines)

                # Prefixa cada linha com o número da linha (base 1)
                enumerated_documentation = "".join(f"{i+1}: {line}" for i, line in enumerate(lines))

                return documentation, enumerated_documentation
        except Exception as e:
            raise ValueError(f"Erro ao ler o arquivo de documentação: {e}")
    else:
        logging.error(f"Aviso: Arquivo de documentação não encontrado em {doc_path}")
        raise ValueError(f"Aviso: Arquivo de documentação não encontrado em {doc_path}")

def update_documentation_with_llm(commit_diff, documentation_content):
    """
    Usa uma LLM (via LangChain) para gerar/atualizar documentação
    com base no diff do commit e no conteúdo de documentação atual.
    Retorna a string com o texto de documentação sugerido.
    """

    # Prompt template para a LLM gerar um json com a documentação a partir do diff do commit
    prompt_template_str = """
    Você é um assistente especializado em gerar documentação de software.
    Receba o diff do commit e o conteúdo atual da documentação e atualize ou adicione
    linhas que reflitam as alterações feitas no commit.

    Diff do commit:
    {commit_diff}

    Instrução:
    Para cada alteração identificada, faça o seguinte:
    1. Determine a linha inicial e a linha final (usando a contagem a partir de 1) no conteúdo atual da documentação onde a alteração deve ser aplicada.
    2. Gere o novo conteúdo que deverá substituir o trecho identificado ou ser inserido nesse local. **O novo conteúdo DEVE estar formatado em Markdown**, utilizando as convenções do Markdown (como cabeçalhos, listas, ênfases, etc.), conforme necessário.

    Sua resposta DEVE ser um JSON válido, sem nenhum comentário ou explicação adicional, no seguinte formato:

    {example}

    Certifique-se de:
    - Utilizar apenas números inteiros para "inicio" e "fim".
    - Incluir apenas o JSON na resposta, sem textos extras.
    - Mantenha o estilo da documentação atual, incluindo cabeçalhos, listas, ênfases, etc.

    Documentação existente:
    {documentation_content}
    Obs.: As linhas estão numeradas para referência, mas não devem ser parte da resposta.
    """

    prompt = PromptTemplate(
        input_variables=["commit_diff", "documentation_content"],
        template=prompt_template_str
    )

    example = """
    {
    "alteracoes": [
        {
        "inicio": 17,
        "fim": 19,
        "novo_conteudo": "# Guia de Instalação  \nExecute o comando abaixo para configurar o ambiente:  \nbash install.sh \nCaso encontre problemas, consulte a seção de **Solução de Problemas**."
        },
        ... // outras alterações, se houver
    ]
    }
    """

    # Cria a instância do modelo LLM, neste caso, o Gemini 2.0 Flash 
    llm = GoogleGenerativeAI(model="gemini-2.0-flash-exp")

    # Cria a cadeia de execução
    chain = (
        RunnablePassthrough.assign(commit_diff=lambda _: commit_diff, documentation_content=lambda _: documentation_content, example=lambda _: example)
        | prompt
        | llm.bind(stop=["\n```"])
        | StrOutputParser()
        | RunnableLambda(lambda x: (x.replace("```json\n", "")))
    )

    try:
        # Executa a cadeia de execução
        changes = chain.invoke({
            "commit_diff": commit_diff,
            "documentation_content": documentation_content
        })
    
        return changes
    except Exception as e:
        logging.error(f"Erro ao atualizar a documentação com a LLM: {e}")
        raise ValueError(f"Erro ao atualizar a documentação com a LLM: {e}")

def update_doc_lines(file_path, changes_json):
    try:
        # Se changes_json for uma string, converte para dict
        if isinstance(changes_json, str):
            changes_json = json.loads(changes_json)
            
        changes = changes_json.get("alteracoes", [])
        
        # Lê o conteúdo do arquivo em uma lista de linhas
        with open(file_path, "r", encoding="utf-8") as file:
            lines = file.readlines()
        
        # Ordena as alterações em ordem decrescente pelo número da linha de início
        # Assim, alterações na parte inferior não interferem nos índices das anteriores.
        changes.sort(key=lambda alt: int(alt["inicio"]), reverse=True)
        
        for change in changes:
            start = int(change["inicio"])
            end = int(change["fim"])
            new_content = change["novo_conteudo"]
            
            # Divide o novo conteúdo em linhas e garante que cada linha termine com \n
            new_lines = new_content.splitlines()
            new_lines = [line + "\n" for line in new_lines]
            
            # Substitui as linhas no intervalo [inicio-1, fim)
            lines[start - 1: end] = new_lines
        
        return lines
        
    except Exception as e:
        logging.error(f"Erro ao atualizar a documentação: {e}")
        raise ValueError(f"Erro ao atualizar a documentação: {e}")
    
def save_documentation_changes(file_path, updated_lines):
    """
    Escreve as linhas atualizadas de volta para o arquivo de documentação.
    """
    try:
        with open(file_path, "w", encoding="utf-8") as file:
            file.writelines(updated_lines)
    except Exception as e:
        logging.error(f"Erro ao salvar as alterações no arquivo: {e}")
        raise ValueError(f"Erro ao salvar as alterações no arquivo: {e}")
    
def create_temp_file(file_path, content):
    """
    Cria um arquivo temporário com o conteúdo fornecido.
    """
    try:
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(content)
    except Exception as e:
        logging.error(f"Erro ao criar o arquivo temporário: {e}")
        raise ValueError(f"Erro ao criar o arquivo temporário: {e}")
    
def clear_temp_file(file_path):
    """
    Limpa o conteúdo de um arquivo temporário.
    """
    try:
        with open(file_path, "w", encoding="utf-8") as file:
            file.write("")
    except Exception as e:
        logging.error(f"Erro ao limpar o arquivo temporário: {e}")
        raise ValueError(f"Erro ao limpar o arquivo temporário: {e}")

def main():
    # Configuração inicial
    repo_path, commit_hash = get_cfg()

    # Inicia o servidor React
    interface = ReactManager(os.path.dirname(os.path.abspath(__file__)))
    interface.start_server()

    # Obtém os arquivos editados no commit
    edited_files = get_edited_files(repo_path, commit_hash)

    server_init()

    # Para cada arquivo editado que tenha documento associado
    for source_file in edited_files:
        # Gera o caminho do arquivo de documentação correspondente
        doc_path = get_doc_path(repo_path, source_file)
        if not doc_path:
            continue

        # Obtém o diff específico para o arquivo de origem
        file_diff = get_file_diff(repo_path, commit_hash, source_file)

        # Lê o conteúdo atual da documentação
        current_documentation, enumerated_documentation = get_documentation_content(doc_path)

        # Atualiza a documentação com base no diff específico
        changes = update_documentation_with_llm(file_diff, enumerated_documentation)

        # Atualiza o conteúdo da documentação no arquivo
        updated_lines = update_doc_lines(doc_path, changes)
        new_documentation = "".join(updated_lines)

        # Verifica se é o último arquivo editado
        last_index = len(edited_files) - 1
        current_index = edited_files.index(source_file)
        continueExec = 0 if current_index == last_index else 1

        # Cria arquivos temporários para exibir as alterações propostas
        create_temp_file(r"..\public\current_documentation.md", current_documentation)
        create_temp_file(r"..\public\new_documentation.md", new_documentation)
        create_temp_file(r"..\public\continue_exec.txt", str(continueExec))

        # Exibe as alterações propostas e solicita aprovação
        approved = approve_changes()

        if approved:
            # Salva as alterações no arquivo
            save_documentation_changes(doc_path, updated_lines)
        
        # Limpa os arquivos temporários
        clear_temp_file(r"..\public\current_documentation.md")
        clear_temp_file(r"..\public\new_documentation.md")
        clear_temp_file(r"..\public\continue_exec.txt")
        
    # Finaliza o servidor React
    interface.stop_server()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logging.error(f"Erro ao executar o script: {e}")
        sys.exit(1)
