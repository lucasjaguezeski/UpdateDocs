import React, { useState, useEffect } from 'react';
import CodeBlock from './CodeBlock';

// Configurações
const API_URL = 'http://localhost:5000/approve_changes';
const DOCUMENTATION_FILES = {
  current: 'current_documentation.md',
  new: 'new_documentation.md'
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

function App() {
  const [documentation, setDocumentation] = useState({
    current: '',
    new: '',
    isLoading: true,
    error: null
  });

  useEffect(() => {
    let isMounted = true;
    let retryTimer = null;

    const fetchWithRetry = async () => {
      try {
        const [currentDoc, newDoc] = await Promise.all([
          fetchText(DOCUMENTATION_FILES.current),
          fetchText(DOCUMENTATION_FILES.new)
        ]);

        // Verifica se os arquivos têm conteúdo
        if (!currentDoc.trim() || !newDoc.trim()) {
          throw new Error('Arquivos vazios');
        }

        if (isMounted) {
          setDocumentation({
            current: currentDoc,
            new: newDoc,
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
      const response = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ Approved: isApproved })
      });

      if (!response.ok) throw new Error('Request failed');

      const result = await response.json();
      console.log('Server response:', result);
      console.log(`Documentation ${isApproved ? 'approved' : 'rejected'}!`);
    } catch (error) {
      console.error('Approval error:', error);
    } finally {
      window.close();
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
          />
        </div>

        <div className="panel panel-right">
          <CodeBlock
            title="New documentation:"
            code={documentation.new}
            language="markdown"
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