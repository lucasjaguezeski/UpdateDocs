import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';

function CodeBlock({ code, language = '', title = '', alteracoes = [], tipo = 'atual' }) {
  // Se não há alterações, renderiza o CodeBlock normal
  if (!alteracoes || alteracoes.length === 0) {
    return (
      <div className="custom-code-block-wrapper">
        {title && <h3 className="custom-code-block-header">{title}</h3>}
        {language.toLowerCase() === 'markdown' ? (
          <div className="custom-code-block">
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              components={{
                code({ node, inline, className, children, ...props }) {
                  const match = /language-(\w+)/.exec(className || '');
                  return !inline && match ? (
                    <SyntaxHighlighter
                      style={vscDarkPlus}
                      language={match[1]}
                      PreTag="div"
                      {...props}
                    >
                      {String(children).replace(/\n$/, '')}
                    </SyntaxHighlighter>
                  ) : (
                    <code className={className} {...props}>
                      {children}
                    </code>
                  );
                }
              }}
            >
              {code}
            </ReactMarkdown>
          </div>
        ) : (
          <pre className={`custom-code-block language-${language}`}>
            <code>{code}</code>
          </pre>
        )}
      </div>
    );
  }

  // Com alterações, precisamos dividir o código em segmentos
  const linhas = code.split('\n');
  const segmentos = [];
  let ultimoIndex = 0;

  // Ordenar as alterações por linha de início
  const alteracoesOrdenadas = [...alteracoes].sort((a, b) => a.inicio - b.inicio);

  // Ajuste para compensar a diferença de indexação 
  const ajustarIndice = (indice) => Math.max(0, indice - 1);

  // Criar segmentos baseados nas alterações
  alteracoesOrdenadas.forEach((alteracao) => {
    // Ajustar os índices de início e fim (converter de base-1 para base-0)
    const inicioAjustado = ajustarIndice(alteracao.inicio);
    const fimAjustado = ajustarIndice(alteracao.fim);
    
    // Segmento antes da alteração
    if (inicioAjustado > ultimoIndex) {
      segmentos.push({
        linhas: linhas.slice(ultimoIndex, inicioAjustado),
        tipo: 'normal'
      });
    }

    // Segmento da alteração
    if (tipo === 'atual') {
      // Para a documentação atual, destacamos o que foi removido (em vermelho)
      segmentos.push({
        linhas: linhas.slice(inicioAjustado, fimAjustado + 1),
        tipo: 'removido'
      });
    } else {
      // Para a nova documentação, destacamos o que foi adicionado (em verde)
      segmentos.push({
        linhas: [alteracao.novo_conteudo],
        tipo: 'adicionado'
      });
    }

    ultimoIndex = fimAjustado + 1;
  });

  // Adicionar o segmento final após todas as alterações
  if (ultimoIndex < linhas.length) {
    segmentos.push({
      linhas: linhas.slice(ultimoIndex),
      tipo: 'normal'
    });
  }

  return (
    <div className="custom-code-block-wrapper">
      {title && <h3 className="custom-code-block-header">{title}</h3>}
      
      {language.toLowerCase() === 'markdown' ? (
        <div className="custom-segments-container">
          {segmentos.map((segmento, index) => (
            <div 
              key={index} 
              className={`custom-code-block ${
                segmento.tipo === 'removido' 
                  ? 'highlighted-block-red' 
                  : segmento.tipo === 'adicionado' 
                    ? 'highlighted-block-green' 
                    : ''
              }`}
            >
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{
                  code({ node, inline, className, children, ...props }) {
                    const match = /language-(\w+)/.exec(className || '');
                    return !inline && match ? (
                      <SyntaxHighlighter
                        style={vscDarkPlus}
                        language={match[1]}
                        PreTag="div"
                        {...props}
                      >
                        {String(children).replace(/\n$/, '')}
                      </SyntaxHighlighter>
                    ) : (
                      <code className={className} {...props}>
                        {children}
                      </code>
                    );
                  }
                }}
              >
                {segmento.linhas.join('\n')}
              </ReactMarkdown>
            </div>
          ))}
        </div>
      ) : (
        <div className="custom-segments-container">
          {segmentos.map((segmento, index) => (
            <pre 
              key={index} 
              className={`custom-code-block language-${language} ${
                segmento.tipo === 'removido' 
                  ? 'highlighted-block-red' 
                  : segmento.tipo === 'adicionado' 
                    ? 'highlighted-block-green' 
                    : ''
              }`}
            >
              <code>{segmento.linhas.join('\n')}</code>
            </pre>
          ))}
        </div>
      )}
    </div>
  );
}

export default CodeBlock;