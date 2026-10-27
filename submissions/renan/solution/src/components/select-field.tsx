import { ChevronDown } from "lucide-react";

/** Select nativo em pílula, com rótulo. Funciona sem JavaScript (form GET). */
export function SelectField({
  name,
  label,
  value,
  options,
  allLabel,
  className = "",
}: {
  name: string;
  label: string;
  value?: string;
  options: readonly { value: string; label: string }[];
  allLabel: string;
  className?: string;
}) {
  return (
    <label className={`flex min-w-[10rem] flex-col gap-1.5 ${className}`}>
      <span className="field">{label}</span>
      <span className="relative">
        <select
          name={name}
          defaultValue={value ?? ""}
          className="h-11 w-full cursor-pointer rounded-full border border-line bg-surface pr-10 pl-4 text-[15px] text-primary hover:border-secondary/50 focus:border-moment focus:outline-none"
        >
          <option value="">{allLabel}</option>
          {options.map((o) => (
            <option key={o.value} value={o.value}>
              {o.label}
            </option>
          ))}
        </select>
        <ChevronDown className="pointer-events-none absolute top-1/2 right-4 size-4 -translate-y-1/2 text-secondary" aria-hidden />
      </span>
    </label>
  );
}

export const asOptions = (values: readonly string[]) => values.map((v) => ({ value: v, label: v }));

export function SubmitButton({ children }: { children: React.ReactNode }) {
  return (
    <button type="submit" className="h-11 cursor-pointer rounded-full bg-primary px-5 text-[15px] font-semibold text-surface hover:opacity-90">
      {children}
    </button>
  );
}
