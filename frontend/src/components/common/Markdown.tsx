import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

/**
 * Safe Markdown rendering: react-markdown does not render raw HTML (no
 * rehype-raw), and links are restricted to http(s)/mailto and opened with
 * rel="noopener noreferrer".
 */
const SAFE_URL = /^(https?:|mailto:|#|\/)/i;

export function Markdown({ content }: { content: string }) {
  return (
    <div className="md-content">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        skipHtml
        urlTransform={(url) => (SAFE_URL.test(url) ? url : "")}
        components={{
          a: ({ children, href }) => (
            <a href={href} target="_blank" rel="noopener noreferrer">
              {children}
            </a>
          ),
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
}
