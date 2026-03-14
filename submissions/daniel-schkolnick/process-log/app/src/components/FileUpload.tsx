import React, { useCallback } from "react";
import { useData } from "@/context/DataContext";
import { Upload } from "lucide-react";

export function FileUpload() {
  const { uploadFile } = useData();

  const handleChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) uploadFile(file);
  }, [uploadFile]);

  return (
    <label className="flex items-center gap-2 px-3 py-2 rounded-md text-xs font-medium text-muted-foreground
      hover:bg-accent hover:text-accent-foreground cursor-pointer transition-colors">
      <Upload className="w-4 h-4" />
      <span>Trocar Planilha</span>
      <input type="file" accept=".xlsx,.xls" onChange={handleChange} className="hidden" />
    </label>
  );
}
