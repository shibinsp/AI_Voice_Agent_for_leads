import type { ReactNode } from "react";

interface PanelProps {
  id?: string;
  title: string;
  eyebrow?: string;
  subtitle?: string;
  actions?: ReactNode;
  children: ReactNode;
  className?: string;
}

export function Panel({
  id,
  title,
  eyebrow,
  subtitle,
  actions,
  children,
  className,
}: PanelProps) {
  const classes = className ? `panel ${className}` : "panel";

  return (
    <section id={id} className={classes}>
      <header className="panel-header">
        <div className="panel-heading">
          {eyebrow ? <span className="panel-eyebrow">{eyebrow}</span> : null}
          <h2>{title}</h2>
          {subtitle ? <p>{subtitle}</p> : null}
        </div>
        {actions ? <div className="panel-actions">{actions}</div> : null}
      </header>
      {children}
    </section>
  );
}
