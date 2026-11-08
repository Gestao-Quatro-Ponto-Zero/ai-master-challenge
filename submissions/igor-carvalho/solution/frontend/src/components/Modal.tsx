import React from 'react';

interface Props {
  /** Nome acessível do diálogo. */
  label: string;
  onClose: () => void;
  children: React.ReactNode;
}

const FOCUSABLE = 'button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])';

/** Diálogo modal: fecha com Esc, mantém o Tab dentro dele e devolve o foco ao fechar. */
export default class Modal extends React.Component<Props> {
  private dialogRef = React.createRef<HTMLDivElement>();
  private closeRef = React.createRef<HTMLButtonElement>();
  private previouslyFocused: Element | null = null;

  componentDidMount() {
    this.previouslyFocused = document.activeElement;
    this.closeRef.current?.focus();
    document.addEventListener('keydown', this.onKeyDown);
  }

  componentWillUnmount() {
    document.removeEventListener('keydown', this.onKeyDown);
    if (this.previouslyFocused instanceof HTMLElement) this.previouslyFocused.focus();
  }

  private onKeyDown = (event: KeyboardEvent) => {
    if (event.key === 'Escape') {
      event.preventDefault();
      this.props.onClose();
      return;
    }
    if (event.key !== 'Tab' || !this.dialogRef.current) return;
    const items = Array.from(this.dialogRef.current.querySelectorAll<HTMLElement>(FOCUSABLE));
    if (items.length === 0) return;
    const first = items[0];
    const last = items[items.length - 1];
    const active = document.activeElement;
    if (event.shiftKey && active === first) {
      event.preventDefault();
      last.focus();
    } else if (!event.shiftKey && active === last) {
      event.preventDefault();
      first.focus();
    }
  };

  render() {
    const { label, onClose, children } = this.props;
    return (
      <div role="dialog" aria-modal="true" aria-label={label} className="modal" ref={this.dialogRef}>
        <div className="modal__backdrop" onClick={onClose} aria-hidden="true" />
        <div className="modal__box">
          <button type="button" className="modal__close" aria-label="Fechar" onClick={onClose} ref={this.closeRef}>
            ×
          </button>
          {children}
        </div>
      </div>
    );
  }
}
