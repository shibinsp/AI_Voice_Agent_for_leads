import { type FormEvent, startTransition, useState } from "react";
import { Bot, Building2, HeartPulse, Home, Save } from "lucide-react";

import type { AgentCreate } from "../types/api";
import { Panel } from "./Panel";

interface AgentStudioProps {
  onCreate: (payload: AgentCreate) => void;
  isCreating: boolean;
  error?: string;
}

interface AgentFormState {
  name: string;
  script_key: string;
  vertical: string;
  language: string;
  voice_provider: string;
  telephony_provider: string;
  description: string;
  opening_line: string;
  qualification_goal: string;
  is_active: boolean;
}

const DEFAULT_FORM: AgentFormState = {
  name: "Hyderabad Clinic Qualifier",
  script_key: "clinic_telugu_v1",
  vertical: "clinics",
  language: "te-IN",
  voice_provider: "sarvam",
  telephony_provider: "mock",
  description: "First response agent for high-intent clinic appointment leads.",
  opening_line: "Namaskaram, I am calling about the appointment request you submitted.",
  qualification_goal: "Capture specialty, urgency, location, and preferred callback window.",
  is_active: true,
};

const TEMPLATES = [
  {
    id: "clinics",
    label: "Clinic",
    icon: HeartPulse,
    form: DEFAULT_FORM,
  },
  {
    id: "real_estate",
    label: "Real Estate",
    icon: Home,
    form: {
      name: "Real Estate Site Visit Agent",
      script_key: "real_estate_visit_v1",
      vertical: "real_estate",
      language: "te-IN",
      voice_provider: "sarvam",
      telephony_provider: "mock",
      description: "Qualifies property inquiries and routes serious leads for site visits.",
      opening_line: "Namaskaram, I am calling about the property inquiry you submitted.",
      qualification_goal: "Capture preferred location, budget range, property type, and visit timing.",
      is_active: true,
    },
  },
  {
    id: "education",
    label: "Education",
    icon: Building2,
    form: {
      name: "Admissions Demo Agent",
      script_key: "education_admission_v1",
      vertical: "education",
      language: "te-IN",
      voice_provider: "sarvam",
      telephony_provider: "mock",
      description: "Calls admission leads and books counseling or demo sessions.",
      opening_line: "Namaskaram, I am calling about the course inquiry you submitted.",
      qualification_goal: "Capture course interest, student stage, availability, and next-step intent.",
      is_active: true,
    },
  },
] as const;

export function AgentStudio({ onCreate, isCreating, error }: AgentStudioProps) {
  const [form, setForm] = useState<AgentFormState>(DEFAULT_FORM);

  function handleTemplate(template: (typeof TEMPLATES)[number]): void {
    startTransition(() => {
      setForm(template.form);
    });
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>): void {
    event.preventDefault();
    onCreate({
      ...form,
      vertical: form.vertical || null,
      description: form.description || null,
      opening_line: form.opening_line || null,
      qualification_goal: form.qualification_goal || null,
    });
  }

  return (
    <Panel
      id="studio"
      title="Agent Studio"
      eyebrow="Create"
      subtitle="Configure a Telugu voice agent that can be selected by new lead campaigns."
    >
      <div className="template-row" role="list" aria-label="Agent templates">
        {TEMPLATES.map((template) => {
          const Icon = template.icon;
          const isSelected = form.vertical === template.form.vertical;

          return (
            <button
              key={template.id}
              className={isSelected ? "template-button is-selected" : "template-button"}
              type="button"
              onClick={() => handleTemplate(template)}
              aria-pressed={isSelected}
            >
              <Icon size={16} />
              <span>{template.label}</span>
            </button>
          );
        })}
      </div>

      <form className="agent-form" onSubmit={handleSubmit}>
        <label className="field">
          <span>Agent Name</span>
          <input
            value={form.name}
            onChange={(event) => setForm({ ...form, name: event.target.value })}
            required
          />
        </label>

        <label className="field">
          <span>Script Key</span>
          <input
            value={form.script_key}
            onChange={(event) => setForm({ ...form, script_key: event.target.value })}
            required
          />
        </label>

        <div className="form-grid">
          <label className="field">
            <span>Vertical</span>
            <select
              value={form.vertical}
              onChange={(event) => setForm({ ...form, vertical: event.target.value })}
            >
              <option value="clinics">Clinics</option>
              <option value="real_estate">Real Estate</option>
              <option value="education">Education</option>
              <option value="insurance">Insurance</option>
              <option value="automotive">Automotive</option>
            </select>
          </label>

          <label className="field">
            <span>Language</span>
            <select
              value={form.language}
              onChange={(event) => setForm({ ...form, language: event.target.value })}
            >
              <option value="te-IN">Telugu</option>
              <option value="hi-IN">Hindi</option>
              <option value="en-IN">English</option>
            </select>
          </label>
        </div>

        <div className="form-grid">
          <label className="field">
            <span>Voice</span>
            <select
              value={form.voice_provider}
              onChange={(event) => setForm({ ...form, voice_provider: event.target.value })}
            >
              <option value="sarvam">Sarvam</option>
              <option value="google">Google</option>
              <option value="manual">Manual</option>
            </select>
          </label>

          <label className="field">
            <span>Telephony</span>
            <select
              value={form.telephony_provider}
              onChange={(event) =>
                setForm({ ...form, telephony_provider: event.target.value })
              }
            >
              <option value="mock">Mock</option>
              <option value="exotel">Exotel</option>
              <option value="plivo">Plivo</option>
            </select>
          </label>
        </div>

        <label className="field">
          <span>Description</span>
          <textarea
            value={form.description}
            onChange={(event) => setForm({ ...form, description: event.target.value })}
            rows={3}
          />
        </label>

        <label className="field">
          <span>Opening Line</span>
          <textarea
            value={form.opening_line}
            onChange={(event) => setForm({ ...form, opening_line: event.target.value })}
            rows={3}
          />
        </label>

        <label className="field">
          <span>Qualification Goal</span>
          <textarea
            value={form.qualification_goal}
            onChange={(event) => setForm({ ...form, qualification_goal: event.target.value })}
            rows={3}
          />
        </label>

        <label className="toggle-field">
          <input
            type="checkbox"
            checked={form.is_active}
            onChange={(event) => setForm({ ...form, is_active: event.target.checked })}
          />
          <span>Active for new campaigns</span>
        </label>

        {error ? <p className="inline-error">{error}</p> : null}

        <button className="primary-button" type="submit" disabled={isCreating}>
          {isCreating ? <Bot size={16} className="spin" /> : <Save size={16} />}
          {isCreating ? "Creating..." : "Create Agent"}
        </button>
      </form>
    </Panel>
  );
}
