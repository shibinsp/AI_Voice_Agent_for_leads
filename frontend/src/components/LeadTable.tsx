import { UserRoundSearch } from "lucide-react";

import type { LeadRead } from "../types/api";
import { EmptyState } from "./EmptyState";
import { Panel } from "./Panel";
import { StatusPill } from "./StatusPill";

interface LeadTableProps {
  leads: LeadRead[];
  total: number;
  isLoading: boolean;
  filterLabel: string;
}

export function LeadTable({
  leads,
  total,
  isLoading,
  filterLabel,
}: LeadTableProps) {
  return (
    <Panel
      id="leads"
      title="Enquiries & Leads"
      eyebrow="Incoming"
      subtitle={`${total} total enquiries in storage. Showing ${filterLabel}.`}
    >
      <div className="table-wrap">
        <table className="data-table">
          <thead>
            <tr>
              <th>Lead</th>
              <th>Contact</th>
              <th>Requirement</th>
              <th>Status</th>
              <th>City</th>
              <th>Created</th>
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              <tr>
                <td colSpan={6} className="table-empty">
                  <div className="skeleton-stack" aria-label="Loading leads">
                    <span />
                    <span />
                    <span />
                  </div>
                </td>
              </tr>
            ) : leads.length === 0 ? (
              <tr>
                <td colSpan={6} className="table-empty">
                  <EmptyState
                    icon={UserRoundSearch}
                    title="No enquiries yet"
                    detail="Share your enquiry link on LinkedIn/Instagram, or use the webhook simulator, to populate this feed."
                  />
                </td>
              </tr>
            ) : (
              leads.map((lead) => (
                <tr key={lead.id}>
                  <td>
                    <div className="primary-cell">
                      <strong>{lead.full_name ?? "Unnamed lead"}</strong>
                      <span>{sourceLabel(lead) ?? lead.external_lead_id}</span>
                    </div>
                  </td>
                  <td>
                    <div className="primary-cell">
                      <strong>{lead.phone_number ?? "No phone"}</strong>
                      <span>{lead.email ?? lead.preferred_language}</span>
                    </div>
                  </td>
                  <td className="requirement-cell">{requirementOf(lead) ?? "—"}</td>
                  <td>
                    <StatusPill status={lead.status} />
                  </td>
                  <td>{lead.city ?? "Hyderabad"}</td>
                  <td>
                    <time dateTime={lead.created_at}>{formatTimestamp(lead.created_at)}</time>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </Panel>
  );
}

function requirementOf(lead: LeadRead): string | null {
  const value = lead.raw_fields?.requirement;
  return typeof value === "string" && value.trim() ? value.trim() : null;
}

function sourceLabel(lead: LeadRead): string | null {
  const source = lead.raw_fields?.source;
  if (source === "linkedin") return "via LinkedIn enquiry";
  if (source === "instagram") return "via Instagram enquiry";
  if (lead.raw_fields?.channel === "enquiry_link") return "via enquiry link";
  return null;
}

function formatTimestamp(value: string): string {
  return new Intl.DateTimeFormat("en-IN", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}
