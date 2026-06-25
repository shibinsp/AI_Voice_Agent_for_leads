import { useState } from "react";
import { Copy, Check, Share2 } from "lucide-react";

import { Panel } from "./Panel";

const CHANNELS: Array<{ key: string; label: string; src: string }> = [
  { key: "linkedin", label: "LinkedIn", src: "linkedin" },
  { key: "instagram", label: "Instagram", src: "instagram" },
  { key: "generic", label: "Generic", src: "" },
];

function enquiryUrl(src: string): string {
  const origin = typeof window !== "undefined" ? window.location.origin : "";
  return src ? `${origin}/enquiry?src=${src}` : `${origin}/enquiry`;
}

export function EnquiryLinkCard() {
  const [copied, setCopied] = useState<string | null>(null);

  async function copy(channelKey: string, url: string): Promise<void> {
    try {
      await navigator.clipboard.writeText(url);
      setCopied(channelKey);
      window.setTimeout(() => setCopied((c) => (c === channelKey ? null : c)), 1800);
    } catch {
      setCopied(null);
    }
  }

  return (
    <Panel
      title="Enquiry Link"
      eyebrow="Share"
      subtitle="Paste this link in your LinkedIn or Instagram post. Anyone who clicks it can submit an enquiry and the AI agent will call them instantly."
    >
      <div className="enquiry-link-list">
        {CHANNELS.map((channel) => {
          const url = enquiryUrl(channel.src);
          return (
            <div key={channel.key} className="enquiry-link-row">
              <div className="enquiry-link-meta">
                <strong>{channel.label}</strong>
                <code>{url}</code>
              </div>
              <button
                className="ghost-button"
                type="button"
                onClick={() => void copy(channel.key, url)}
              >
                {copied === channel.key ? <Check size={14} /> : <Copy size={14} />}
                {copied === channel.key ? "Copied" : "Copy"}
              </button>
            </div>
          );
        })}
      </div>
      <a className="enquiry-link-open" href={enquiryUrl("")} target="_blank" rel="noreferrer">
        <Share2 size={14} />
        Open the enquiry page
      </a>
    </Panel>
  );
}
