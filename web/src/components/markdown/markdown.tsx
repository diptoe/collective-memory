import ReactMarkdown from 'react-markdown';
import { cn } from '@/lib/utils';

interface MarkdownProps {
  content: string;
  className?: string;
}

/**
 * Safe markdown renderer (no raw HTML).
 * Kept intentionally lightweight; we can add GFM later if needed.
 */
export function Markdown({ content, className }: MarkdownProps) {
  return (
    <div className={cn('text-sm break-words', className)}>
      <ReactMarkdown
        skipHtml
        components={{
          h1: ({ children }) => <h1 className="text-base font-semibold mt-2 mb-2">{children}</h1>,
          h2: ({ children }) => <h2 className="text-sm font-semibold mt-2 mb-2">{children}</h2>,
          h3: ({ children }) => <h3 className="text-sm font-medium mt-2 mb-2">{children}</h3>,
          p: ({ children }) => (
            <p className="leading-relaxed whitespace-pre-wrap mb-2 last:mb-0">{children}</p>
          ),
          a: ({ href, children }) => (
            <a
              href={href}
              target="_blank"
              rel="noreferrer"
              className="underline underline-offset-2 text-cm-coffee"
            >
              {children}
            </a>
          ),
          ul: ({ children }) => <ul className="list-disc pl-5 mb-2 last:mb-0">{children}</ul>,
          ol: ({ children }) => <ol className="list-decimal pl-5 mb-2 last:mb-0">{children}</ol>,
          li: ({ children }) => <li className="mb-1 last:mb-0">{children}</li>,
          blockquote: ({ children }) => (
            <blockquote className="border-l-2 border-cm-coffee/30 pl-3 italic my-2">
              {children}
            </blockquote>
          ),
          pre: ({ children }) => (
            <pre className="my-2 overflow-x-auto rounded-md p-3 text-xs bg-black/5">
              {children}
            </pre>
          ),
          code: ({ className, children }) => {
            const isBlock = typeof className === 'string' && className.includes('language-');
            const text = String(children).replace(/\n$/, '');
            return (
              <code className={cn('font-mono', isBlock ? 'text-xs' : 'rounded px-1 py-0.5 bg-black/5')}>
                {text}
              </code>
            );
          },
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
}

