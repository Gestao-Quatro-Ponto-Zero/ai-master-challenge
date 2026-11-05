import { FileDown, FileSpreadsheet } from "lucide-react";

export function ExportButtons({ onPdf, onXlsx, disabled }: { onPdf: () => void; onXlsx: () => void; disabled?: boolean }) {
  return (
    <div className="flex items-center gap-2">
      <button
        onClick={onPdf}
        disabled={disabled}
        className="inline-flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50"
      >
        <FileDown className="h-4 w-4" />
        Exportar PDF
      </button>
      <button
        onClick={onXlsx}
        disabled={disabled}
        className="inline-flex items-center gap-2 rounded-md border border-border bg-card px-4 py-2 text-sm font-medium text-foreground transition-colors hover:bg-accent disabled:cursor-not-allowed disabled:opacity-50"
      >
        <FileSpreadsheet className="h-4 w-4" />
        Exportar XLSX
      </button>
    </div>
  );
}
