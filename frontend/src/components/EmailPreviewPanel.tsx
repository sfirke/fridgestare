import type { EmailPreview } from '../types/api';

export function EmailPreviewPanel({ preview }: { preview: EmailPreview | null }) {
  return (
    <div className="panel-subsection">
      <div className="section-header-inline">
        <h3>Email preview</h3>
        {preview ? <span className="subtle-copy">{preview.delivery_mode}</span> : null}
      </div>
      {preview ? (
        <>
          <p className="slot-meta">{preview.subject}</p>
          {/*
            Rendered in a sandboxed iframe rather than injected into the page. The email
            body is a full HTML document with its own <body> styling, and inlining it let
            that leak into the app; the sandbox also stops any future template change from
            running script in the app's origin.
          */}
          <iframe
            className="email-preview"
            title={`Email preview: ${preview.subject}`}
            sandbox=""
            srcDoc={preview.html}
          />
        </>
      ) : (
        <p className="subtle-copy">Preview the weekly summary email from the planner panel.</p>
      )}
    </div>
  );
}
