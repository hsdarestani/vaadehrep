import { ReactNode } from "react";

type Props = {
  title: string;
  description?: string;
  footer?: ReactNode;
  children?: ReactNode;
};

export function Card({ title, description, footer, children }: Props) {
  return (
    <div className="card">
      <h3>{title}</h3>
      {description ? <p className="muted">{description}</p> : null}
      {children}
      {footer ? <div style={{ marginTop: 12 }}>{footer}</div> : null}
    </div>
  );
}
