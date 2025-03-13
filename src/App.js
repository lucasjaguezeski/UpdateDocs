import React, { useState, useEffect } from 'react';
import CodeBlock from './CodeBlock';

// Configurações
const API_URL = 'http://localhost:5000/approve_changes';
const DOCUMENTATION_FILES = {
  current: 'current_documentation.md',
  continue_exec: 'continue_exec.txt',
  alteracoes: 'alteracoes.json' 
};

const RETRY_INTERVAL = 3000;

// Error Boundary para capturar e logar erros
class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false };
  }
  
  static getDerivedStateFromError(error) {
    return { hasError: true };
  }
  
  componentDidCatch(error, errorInfo) {
    console.error("Erro:", error, errorInfo);
    // Futura implementação: enviar log de erro para um serviço de monitoramento
  }
  
  render() {
    if (this.state.hasError) {
      return <h2>Ops, ocorreu um erro.</h2>;
    }
    return this.props.children;
  }
}

const aplicarAlteracoes = (textoOriginal, alteracoes) => {
  // Aplicar as alterações no texto da mesma forma que o CodeBlock.js
  const linhas = textoOriginal.split('\n');
  const alteracoesOrdenadas = [...alteracoes].sort((a, b) => a.inicio - b.inicio);
  
  // Array com segmentos do texto final
  let resultado = [...linhas];
  
  // Aplicar cada alteração na ordem inversa para não afetar os índices
  [...alteracoesOrdenadas].reverse().forEach(alteracao => {
    // Ajustar índices para base-0
    const inicioAjustado = Math.max(0, alteracao.inicio - 1);
    const fimAjustado = Math.max(0, alteracao.fim - 1);
    
    // Substituir o segmento pelo novo conteúdo
    resultado.splice(inicioAjustado, fimAjustado - inicioAjustado + 1, alteracao.novo_conteudo);
  });
  
  return resultado.join('\n');
};

function App() {
  const [documentation, setDocumentation] = useState({
    current: '',
    alteracoes: [],
    isLoading: true,
    error: null
  });

  useEffect(() => {
    let isMounted = true;
    let retryTimer = null;

    const fetchWithRetry = async () => {
      try {
        const [currentDoc, continueExec, alteracoesText] = await Promise.all([
          fetchText(DOCUMENTATION_FILES.current),
          fetchText(DOCUMENTATION_FILES.continue_exec),
          fetchText(DOCUMENTATION_FILES.alteracoes).catch(err => '{"alteracoes":[]}')
        ]);
    
        if (!currentDoc.trim()) {
          throw new Error('Arquivo vazio');
        }
    
        let alteracoes = [];
        try {
          const alteracoesObj = JSON.parse(alteracoesText);
          alteracoes = alteracoesObj.alteracoes || [];
        } catch (error) {
          console.warn('Erro ao analisar alterações JSON:', error);
        }
    
        if (isMounted) {
          setDocumentation({
            current: currentDoc,
            alteracoes: alteracoes,
            continueExec: parseInt(continueExec),
            isLoading: false,
            error: null
          });
        }
      } catch (error) {
        if (isMounted) {
          console.log(`Tentativa falhou: ${error.message}. Tentando novamente em ${RETRY_INTERVAL/1000} segundos...`);
          setDocumentation(prev => ({
            ...prev,
            isLoading: true,
            error: `Aguardando arquivos... (${error.message})`
          }));
          
          // Agenda nova tentativa
          retryTimer = setTimeout(fetchWithRetry, RETRY_INTERVAL);
        }
      }
    };

    const fetchText = async (filename) => {
      const response = await fetch(filename);
      if (!response.ok) throw new Error(`Arquivo não encontrado: ${filename}`);
      return await response.text();
    };

    fetchWithRetry();

    return () => {
      isMounted = false;
      clearTimeout(retryTimer);
    };
  }, []);

  const handleApproval = async (isApproved) => {
    try {
      // Obter o texto final com alterações aplicadas (se aprovado)
      const finalText = isApproved 
        ? aplicarAlteracoes(documentation.current, documentation.alteracoes)
        : "";
      
      const response = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          Approved: isApproved,
          Data: finalText
        })
      });
  
      if (!response.ok) throw new Error('Request failed');
  
      const result = await response.json();
      console.log('Server response:', result);
      console.log(`Documentation ${isApproved ? 'approved' : 'rejected'}!`);
    } catch (error) {
      console.error('Approval error:', error);
    } finally {
      if (!documentation.continueExec) {
        window.close();
      }
    }
  };

  if (documentation.isLoading) {
    return (
      <div className="loading">
        <div className="loading-spinner"></div>
        {'Carregando documentação...'}
      </div>
    );
  }

  if (documentation.error) {
    return <div className="error">Error: {documentation.error}</div>;
  }

  return (
    <ErrorBoundary>
      <div className="container">
        <div className="panel panel-left">
          <CodeBlock
            title="Current Documentation:"
            code={documentation.current}
            language="markdown"
            alteracoes={documentation.alteracoes}
            tipo="atual"
          />
        </div>

        <div className="panel panel-right">
          <CodeBlock
            title="Proposed Changes:"
            code={documentation.current}
            language="markdown"
            alteracoes={documentation.alteracoes}
            tipo="novo"
          />
        </div>

        <div className="button-container">
          <button
            className="btn btn-approve"
            onClick={() => handleApproval(true)}
          >
            Approve
          </button>
          <button
            className="btn btn-reject"
            onClick={() => handleApproval(false)}
          >
            Reject
          </button>
        </div>
      </div>
    </ErrorBoundary>
  );
}

export default App;