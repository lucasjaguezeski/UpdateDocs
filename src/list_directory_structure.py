import os

def list_directory_structure(root_path, exclude_patterns=None):
    # Lista padrão de padrões a serem excluídos
    default_exclude = [
        'node_modules', 'venv', '.venv', 'env', '.git', '.gitignore', '__pycache__',
        'build', 'dist', '.next', 'out', 'target', '.idea', '.vscode',
        '.DS_Store', 'coverage', 'logs', 'tmp', 'temp', 'nbproject'
    ]
    
    # Se nenhuma lista for fornecida, use a lista padrão
    if exclude_patterns is None:
        exclude_patterns = default_exclude
    
    # Lista para armazenar os caminhos
    paths = []
    
    # Percorre o diretório raiz e todos os seus subdiretórios
    for dirpath, dirnames, filenames in os.walk(root_path, topdown=True):
        # Filtrar diretórios para não percorrer aqueles que devem ser excluídos
        # Isso precisa ser feito in-place para afetar o os.walk
        dirnames[:] = [d for d in dirnames if d not in exclude_patterns]
        
        # Calcula o caminho relativo ao diretório raiz
        relative_path = os.path.relpath(dirpath, root_path)
        
        # Se o caminho relativo for '.', é o próprio diretório raiz, então deixamos vazio
        if relative_path == '.':
            relative_path = ''
        
        # Adiciona os subdiretórios com '/' no final
        for dirname in dirnames:
            dir_full_path = os.path.join(relative_path, dirname)
            paths.append(dir_full_path + '/')
        
        # Adiciona os arquivos, excluindo os que estão na lista de exclusão
        for filename in filenames:
            if filename not in exclude_patterns:
                file_full_path = os.path.join(relative_path, filename)
                paths.append(file_full_path)
    
    # Ordena os caminhos para consistência
    paths.sort()
    
    # Adiciona o nome do diretório raiz no início de cada caminho
    root_name = os.path.basename(root_path)
    full_paths = [os.path.join(root_name, path).replace('\\', '/') for path in paths]
    
    return '\n'.join(full_paths)
