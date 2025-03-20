# Standard libraries
import logging
import json
import os
from typing import Dict, Any, Optional

# LangChain libraries
from langchain_google_genai import GoogleGenerativeAI
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.messages import HumanMessage, AIMessage
from langchain.memory import ConversationBufferMemory

# Auxiliary functions
from list_directory_structure import list_directory_structure

# Environment variables
from dotenv import load_dotenv
load_dotenv()

# Configuração do log de erros
def setup_logging():
    log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs", "errors.log")
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    logging.basicConfig(
        filename=log_path,
        level=logging.ERROR,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

class DocumentationAssistant:
    def __init__(self, project_path: str):
        setup_logging()
        self.project_path = project_path
        self.model = self._create_model()
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
        self.json_parser = JsonOutputParser(pydantic_object=None)
        
    def _create_model(self) -> GoogleGenerativeAI:
        """Inicializa o modelo de IA."""
        try:
            return GoogleGenerativeAI(
                model="gemini-2.0-flash-exp",
                temperature=0.7
            )
        except Exception as e:
            logging.error(f"Erro ao inicializar o modelo: {e}")
            raise RuntimeError("Não foi possível inicializar o modelo de IA.")
    
    def _enumerate_lines(self, text: str) -> str:
        """Enumera as linhas de um texto."""
        if not text:
            return ""
        
        lines = text.splitlines()
        return "\n".join([f"{i+1}: {line}" for i, line in enumerate(lines)])
    
    def _read_file_content(self, file_path: str) -> Optional[str]:
        """Lê o conteúdo de um arquivo."""
        try:
            # Verificar se o caminho está tentando acessar fora do projeto
            abs_path = os.path.abspath(file_path)
            if not abs_path.startswith(os.path.abspath(self.project_path)):
                logging.error(f"Tentativa de acesso a arquivo fora do projeto: {file_path}")
                return None
            
            # Se o caminho for relativo, converter para absoluto
            if not os.path.isabs(file_path):
                file_path = os.path.join(self.project_path, file_path)
            
            if not os.path.exists(file_path):
                return f"Arquivo não encontrado: {file_path}"
            
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        except Exception as e:
            logging.error(f"Erro ao ler o arquivo {file_path}: {e}")
            return f"Erro ao ler o arquivo: {str(e)}"
    
    def _handle_file_request(self, file_path: str) -> str:
        """
        Processa uma solicitação de arquivo e retorna seu conteúdo 
        com instrução para continuar.
        """
        content = self._read_file_content(file_path)
        if not content:
            return f"Arquivo não encontrado: {file_path}\n\nSe você já tem informações suficientes, responda apenas com 'continue'. Caso contrário, solicite outro arquivo."
        
        enumerated_content = self._enumerate_lines(content)
        
        return (f"Conteúdo do arquivo {file_path}:\n\n{enumerated_content}\n\n"
                f"Se você já tem informações suficientes para sugerir alterações na documentação, "
                f"responda apenas com 'continue'. Caso contrário, solicite outro arquivo.")
    
    def _get_initial_prompt(self) -> str:
        """Retorna o prompt inicial completo."""
        return """
        Você é um assistente especializado em gerar documentação de software.
        Com base no conteúdo do commit diff e da documentação atual, sua tarefa é sugerir alterações na documentação.
        
        Analise cuidadosamente as informações a seguir:
        
        COMMIT DIFF:
        {commit_diff}
        
        DOCUMENTAÇÃO ATUAL (numerada para referência):
        {documentation_content}
        
        INSTRUÇÕES:
        1. Se estas informações forem suficientes para você sugerir alterações na documentação, 
           responda apenas com a palavra "continue".
        
        2. Se precisar examinar algum arquivo específico para ter mais contexto, 
           responda apenas com o nome do arquivo desejado.
           
        A estrutura do projeto para referência:
        {directory_structure}
        """
    
    def _get_final_prompt(self) -> str:
        """Retorna o prompt final para geração de alterações na documentação."""
        return """
        Com base em todas as informações fornecidas, gere sugestões de alterações para a documentação.
        
        Para cada alteração identificada, faça o seguinte:
        1. Determine a linha inicial e a linha final (usando a contagem a partir de 1) no conteúdo atual da documentação onde a alteração deve ser aplicada.
        2. Gere o novo conteúdo que deverá substituir o trecho identificado ou ser inserido nesse local. **O novo conteúdo DEVE estar formatado em Markdown**, utilizando as convenções do Markdown (como cabeçalhos, listas, ênfases, etc.), conforme necessário.

        Sua resposta DEVE ser um JSON válido, sem nenhum comentário ou explicação adicional, no seguinte formato:

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

        Certifique-se de:
        - Utilizar apenas números inteiros para "inicio" e "fim".
        - Incluir apenas o JSON na resposta, sem textos extras.
        - Mantenha o estilo da documentação atual, incluindo cabeçalhos, listas, ênfases, etc.
        """
    
    def process_commit_diff(self, commit_diff: str, documentation_content: str) -> Dict[str, Any]:
        """
        Processa o diff do commit e sugere alterações na documentação.
        
        Args:
            commit_diff: Diferenças do commit
            documentation_content: Conteúdo atual da documentação
            
        Returns:
            Dicionário com sugestões de alterações na documentação
        """
        try:
            # Enumerar linhas da documentação
            enumerated_doc = self._enumerate_lines(documentation_content)
            
            # Obter a estrutura do diretório usando a função importada
            directory_structure = list_directory_structure(self.project_path)
            
            # Iniciar a conversa com o prompt inicial completo
            initial_prompt = self._get_initial_prompt().format(
                commit_diff=commit_diff,
                documentation_content=enumerated_doc,
                directory_structure=directory_structure
            )
            
            # Adicionar a mensagem inicial ao histórico
            human_message = HumanMessage(content=initial_prompt)
            self.memory.chat_memory.messages.append(human_message)
            
            # Obter a primeira resposta da IA
            response_text = self.model.invoke([human_message])
            
            # Criar um objeto AIMessage com a resposta e adicioná-lo ao histórico
            ai_message = AIMessage(content=response_text)
            self.memory.chat_memory.messages.append(ai_message)
            
            # Loop de interação para permitir exploração de arquivos se necessário
            max_iterations = 5  # Limitar o número de iterações para evitar loops
            for i in range(max_iterations):
                # Verificar se a resposta é "continue" (case insensitive e considerando espaços)
                if ai_message.content.strip().lower() == "continue" or ai_message.content.strip().lower() == "continuar":
                    break  # Sair do loop e prosseguir para a geração final
                
                # Verificar se estamos no último loop
                if i == max_iterations - 1:
                    logging.warning(f"Número máximo de iterações atingido sem 'continue'. Última resposta: {ai_message.content}")
                    # Forçar a continuar mesmo assim
                    break
                
                # Caso contrário, tente processar a resposta como um nome de arquivo
                file_path = ai_message.content.strip()
                file_content_message = self._handle_file_request(file_path)
                
                # Adicionar conteúdo do arquivo ao histórico
                human_message = HumanMessage(content=file_content_message)
                self.memory.chat_memory.messages.append(human_message)
                
                # Obter nova resposta
                response_text = self.model.invoke(self.memory.chat_memory.messages)
                
                # Criar um objeto AIMessage com a resposta e adicioná-lo ao histórico
                ai_message = AIMessage(content=response_text)
                self.memory.chat_memory.messages.append(ai_message)
            
            # Somente enviar o final_prompt se a resposta for "continue"
            final_prompt = self._get_final_prompt()
            human_message = HumanMessage(content=final_prompt)
            self.memory.chat_memory.messages.append(human_message)
            
            # Obter a resposta final
            try:
                final_response_text = self.model.invoke(self.memory.chat_memory.messages)
                
                # Criar um objeto AIMessage com a resposta final e adicioná-lo ao histórico
                final_ai_message = AIMessage(content=final_response_text)
                self.memory.chat_memory.messages.append(final_ai_message)
                
                # Parse do JSON
                json_start = final_response_text.find('{')
                json_end = final_response_text.rfind('}') + 1
                
                if json_start >= 0 and json_end > json_start:
                    json_str = final_response_text[json_start:json_end]
                    try:
                        return json.loads(json_str)
                    except json.JSONDecodeError as e:
                        logging.error(f"Erro ao processar JSON: {e}\nJSON string: {json_str}")
                        return {"error": "Formato de resposta inválido", "resposta": final_response_text}
                else:
                    # Tentar usar o JsonOutputParser como fallback
                    try:
                        return self.json_parser.invoke(final_response_text)
                    except Exception as e:
                        logging.error(f"Erro ao processar com JsonOutputParser: {e}")
                        return {"error": "Formato de resposta inválido", "resposta": final_response_text}
                
            except Exception as e:
                logging.error(f"Erro ao obter resposta final: {e}")
                return {"error": str(e)}
            
        except Exception as e:
            logging.error(f"Erro ao processar commit diff: {e}")
            return {"error": str(e)}

# Função principal para ser chamada de outros scripts
def generate_documentation_changes(commit_diff: str, documentation_content: str, project_path: str) -> str:
    """
    Gera sugestões de alterações na documentação com base no diff do commit.
    
    Args:
        commit_diff: Diferenças do commit
        documentation_content: Conteúdo atual da documentação
        project_path: Caminho para a raiz do projeto
        
    Returns:
        JSON com sugestões de alterações
    """
    try:
        assistant = DocumentationAssistant(project_path)
        result = assistant.process_commit_diff(commit_diff, documentation_content)
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as e:
        logging.error(f"Erro ao gerar alterações na documentação: {e}")
        return json.dumps({"error": str(e)})
