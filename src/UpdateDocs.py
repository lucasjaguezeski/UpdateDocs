# Standard libraries
import os
import os.path
import sys
import subprocess
import logging

# Auxiliary Functions
from request import server_init, approve_changes
from interface_controller import ReactManager
from llm_chain import generate_documentation_changes

# Configuração do log de erros
log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs", "errors.log")
os.makedirs(os.path.dirname(log_path), exist_ok=True)
logging.basicConfig(
    filename=log_path,
    level=logging.ERROR,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Extensões de arquivos de código-fonte suportadas
SOURCE_EXTENSIONS = [".java", ".py", ".js", ".ts", ".jsx", ".tsx", ".c",
                  ".cpp", ".cs", ".html", ".rb", ".r", ".php", ".go", ".rs",
                  ".swift", ".sql"] # Pode ser expandido para outras extensões

# Caminhos dos arquivos temporários para exibir as alterações propostas
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CURRENT = os.path.join(base_dir, "public", "current_documentation.md")
ALT = os.path.join(base_dir, "public", "alteracoes.json")
CONTINUE = os.path.join(base_dir, "public", "continue_exec.txt")

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
    Retorna uma lista de nomes de arquivos que possuem extensões definidas em SOURCE_EXTENSIONS.
    """
    try:
        result = subprocess.run(
            ["git", "diff-tree", "--no-commit-id", "--name-only", "-r", commit_hash],
            capture_output=True,
            text=True,
            check=True,
            cwd=repo_path  # Usa o diretório do repositório especificado
        )
        
        files = result.stdout.splitlines()
        return [file for file in files if os.path.splitext(file)[1] in SOURCE_EXTENSIONS]
    
    except subprocess.CalledProcessError as e:
        logging.error(f"Erro ao obter os arquivos editados: {e.stderr}")
        raise ValueError(f"Erro ao obter os arquivos editados: {e.stderr.strip()}")
    
def get_doc_path(repo_path, src_file):
    """
    Gera e retorna o caminho do arquivo de documentação (.md) correspondente a um arquivo de código-fonte.
    Verifica se o arquivo de entrada possui uma das extensões cadastradas e se contém a palavra "src" em seu caminho.
    Caso essas condições sejam atendidas, substitui a extensão origem por ".md" e a pasta "src" por "docs",
    concatenando com o caminho do repositório fornecido. Se não for possível aplicar a transformação, retorna None.
    Parâmetros:
        repo_path (str): Caminho do repositório onde se encontram os arquivos.
        src_file (str): Caminho relativo do arquivo de código-fonte.
    Retorna:
        str ou None: Caminho completo do arquivo de documentação se o arquivo for compatível; caso contrário, None.
    """

    if any(src_file.endswith(ext) for ext in SOURCE_EXTENSIONS) and "src" in src_file:
        for ext in SOURCE_EXTENSIONS:
            if src_file.endswith(ext):
                doc_file_name = src_file.replace(ext, ".md").replace("src", "docs")
                break
        doc_path = (f'{repo_path}/{doc_file_name}')
        if os.path.isfile(doc_path):
            return doc_path
        return None
    return None

def get_documentation_content(doc_path):
    """
    Lê e concatena o conteúdo de uma lista de arquivos de documentação.
    Retorna uma string com o conteúdo dos arquivos selecionados.
    """
    if os.path.isfile(doc_path):
        try:
            with open(doc_path, "r", encoding="utf-8") as doc_file:
                # Lê o conteúdo do arquivo de documentação
                documentation = doc_file.read()

                # Se o arquivo estiver vazio ou não tiver conteúdo, retorna None
                if not documentation:
                    return None
                
                return documentation
        except Exception as e:
            logging.error(f"Erro ao ler o arquivo de documentação: {e}")
            return None
    else:
        logging.error(f"Aviso: Arquivo de documentação não encontrado em {doc_path}")
        return None
    
def manipulate_file(file_paths, operation, contents=None):
    """
    Manipula arquivos com operações específicas.

    Parameters:
    ----------
    file_paths : str ou list
        Caminho(s) do(s) arquivo(s) a ser(em) manipulado(s)
    operation : str
        Tipo de operação: 'write', 'clear', 'delete'
    contents : str, list, None, optional
        Conteúdo(s) a ser(em) escrito(s) no(s) arquivo(s) (para operações de escrita)
    """
    try:
        # Normaliza os parâmetros para listas
        if not isinstance(file_paths, list):
            file_paths = [file_paths]
            
        # Adapta contents para corresponder a file_paths
        if contents is not None and not isinstance(contents, list):
            contents = [contents]
                
        # Processa cada arquivo
        for i, file_path in enumerate(file_paths):
            if operation == "delete":
                os.remove(file_path)
                continue
                
            with open(file_path, "w", encoding="utf-8") as file:
                if operation == "clear":
                    file.write("")
                elif operation == "write":
                    file.write(str(contents[i]) if contents[i] is not None else "ERROR")
                else:
                    logging.error(f"Operação inválida: {operation}")
                    raise ValueError(f"Operação inválida: {operation}")
                    
    except (FileNotFoundError, PermissionError) as e:
        # Captura o nome do arquivo atual
        current_file = file_paths[i] if 'i' in locals() else str(file_paths)
        logging.error(f"{type(e).__name__} ao manipular arquivo: {current_file}: {e}")
        raise
    except Exception as e:
        current_file = file_paths[i] if 'i' in locals() else str(file_paths)
        logging.error(f"Erro ao manipular o arquivo {current_file}: {e}")
        raise ValueError(f"Erro ao manipular o arquivo: {e}")
    
def verify_valid_files(repo_path, edited_files):
    """
    Verifica os arquivos editados para identificar aqueles que possuem documentação válida.

    Parâmetros:
        repo_path (str): O caminho do repositório onde os arquivos estão localizados.
        edited_files (list): Lista de arquivos que foram editados.

    Retorna:
        list: Uma lista de tuplas, onde cada tupla contém:
              (arquivo editado, caminho do arquivo de documentação, conteúdo atual da documentação, documentação enumerada).
              
    Descrição:
        Para cada arquivo na lista 'edited_files', a função obtém o caminho do arquivo de documentação correspondente
        utilizando 'get_doc_path'. Se um caminho é encontrado, são extraídos o conteúdo atual e o conteúdo enumerado da
        documentação por meio da função 'get_documentation_content'. Se ambos os conteúdos forem válidos, a tupla com os
        dados pertinentes é adicionada à lista de arquivos com documentação válida, que é retornada ao final.
    """
    valid_doc_files = []
    for source_file in edited_files:
        doc_path = get_doc_path(repo_path, source_file)
        if doc_path:
            current_documentation = get_documentation_content(doc_path)
            if current_documentation:
                valid_doc_files.append((source_file, doc_path, current_documentation))
    return valid_doc_files

def main():
    # Configuração inicial
    repo_path, commit_hash = get_cfg()

    # Inicia o servidor React
    interface = ReactManager(os.path.dirname(os.path.abspath(__file__)))
    interface.start_server()

    # Obtém os arquivos editados no commit
    edited_files = get_edited_files(repo_path, commit_hash)

    # Verifica quais arquivos editados possuem documentos válidos associados
    valid_doc_files = verify_valid_files(repo_path, edited_files)

    server_init()

    # Para cada arquivo editado que tenha documento associado
    for i, (source_file, doc_path, current_documentation) in enumerate(valid_doc_files):
        # Obtém o diff específico para o arquivo de origem
        file_diff = get_file_diff(repo_path, commit_hash, source_file)

        # Gera as alterações propostas utilizando IA
        changes = generate_documentation_changes(file_diff, current_documentation, repo_path)

        # Verifica se é o último arquivo editado
        continueExec = 0 if i == len(valid_doc_files) - 1 else 1

        # Cria arquivos temporários para exibir as alterações propostas
        manipulate_file([CURRENT, ALT, CONTINUE], "write", contents=[current_documentation, changes, str(continueExec)])

        # Exibe as alterações propostas e solicita aprovação
        approved, new_documentation = approve_changes()

        if approved and new_documentation:
            manipulate_file(doc_path, "write", contents=new_documentation)
        
        # Limpa os arquivos temporários
        manipulate_file([CURRENT, ALT, CONTINUE], "clear")

    # Deleta os arquivos temporários
    manipulate_file([CURRENT, ALT, CONTINUE], "delete")

    # Finaliza o servidor React
    interface.stop_server()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logging.error(f"Erro ao executar o script: {e}")
        sys.exit(1)
