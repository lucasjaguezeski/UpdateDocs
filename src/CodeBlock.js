import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';

function CodeBlock({ code, language = '', title = '' }) {
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

export default CodeBlock;