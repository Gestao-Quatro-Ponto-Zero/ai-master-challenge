"use client";

import { useState, useRef } from "react";
import { api } from "@/lib/api";
import type { OnboardingResponse } from "@/types";
import { Upload, FileSpreadsheet, Check, X, Loader2, Database, AlertCircle } from "lucide-react";

export default function ImportarDadosPage() {
  const fileRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState<OnboardingResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleFile = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    if (f) {
      const valid = f.name.endsWith(".csv") || f.name.endsWith(".xlsx") || f.name.endsWith(".xls");
      if (!valid) {
        setError("Formato inválido. Use CSV ou XLSX.");
        return;
      }
      setFile(f);
      setError(null);
      setResult(null);
    }
  };

  const upload = async () => {
    if (!file) return;
    setUploading(true);
    setError(null);
    setResult(null);
    try {
      const data = await api.uploadDados(file);
      setResult(data);
      setFile(null);
      if (fileRef.current) fileRef.current.value = "";
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Erro ao importar dados");
    } finally {
      setUploading(false);
    }
  };

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-800">Importar Dados</h1>
        <p className="text-sm text-gray-500 mt-1">
          Importe tickets históricos para alimentar a base de conhecimento (RAG)
        </p>
      </div>

      <div className="card mb-6">
        <h3 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
          <Database className="w-4 h-4 text-blue-600" />
          Upload de Arquivo
        </h3>
        <p className="text-xs text-gray-500 mb-4">
          Envie um arquivo CSV ou XLSX com pelo menos uma coluna de texto (ex: &quot;texto&quot;, &quot;Document&quot;, &quot;Ticket Description&quot;).
          Colunas opcionais: &quot;resolucao&quot;/&quot;Resolution&quot;, &quot;categoria&quot;/&quot;Topic_group&quot;.
        </p>

        <div
          className={`border-2 border-dashed rounded-xl p-8 text-center transition-colors ${file ? "border-blue-400 bg-blue-50" : "border-gray-200 hover:border-gray-300"}`}
          onClick={() => fileRef.current?.click()}
          style={{ cursor: "pointer" }}
        >
          <input ref={fileRef} type="file" accept=".csv,.xlsx,.xls" onChange={handleFile} className="hidden" />
          {file ? (
            <div className="flex items-center justify-center gap-3">
              <FileSpreadsheet className="w-8 h-8 text-blue-600" />
              <div className="text-left">
                <p className="text-sm font-medium text-gray-800">{file.name}</p>
                <p className="text-xs text-gray-500">{(file.size / 1024).toFixed(1)} KB</p>
              </div>
            </div>
          ) : (
            <>
              <Upload className="w-10 h-10 text-gray-300 mx-auto mb-3" />
              <p className="text-sm text-gray-500">Clique para selecionar ou arraste um arquivo</p>
              <p className="text-xs text-gray-400 mt-1">CSV, XLSX (até 50MB)</p>
            </>
          )}
        </div>

        {file && (
          <div className="mt-4 flex gap-2">
            <button onClick={upload} disabled={uploading} className="btn-primary text-sm flex items-center gap-2">
              {uploading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Upload className="w-4 h-4" />}
              {uploading ? "Importando..." : "Importar e Indexar"}
            </button>
            <button onClick={() => { setFile(null); if (fileRef.current) fileRef.current.value = ""; }} className="btn-secondary text-sm">
              Cancelar
            </button>
          </div>
        )}
      </div>

      {error && (
        <div className="card mb-6 bg-red-50 border-red-200">
          <div className="flex items-center gap-2 text-red-700">
            <AlertCircle className="w-5 h-5" />
            <span className="text-sm font-medium">Erro na importação</span>
          </div>
          <p className="text-xs text-red-600 mt-2">{error}</p>
        </div>
      )}

      {result && (
        <div className="card bg-green-50 border-green-200">
          <div className="flex items-center gap-2 text-green-700 mb-3">
            <Check className="w-5 h-5" />
            <span className="text-sm font-semibold">Importação Concluída</span>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-white rounded-lg p-3 text-center">
              <p className="text-2xl font-bold text-green-600">{result.registros_importados}</p>
              <p className="text-xs text-gray-500">Registros Importados</p>
            </div>
            <div className="bg-white rounded-lg p-3 text-center">
              <p className="text-2xl font-bold text-blue-600">{result.categorias_encontradas.length}</p>
              <p className="text-xs text-gray-500">Categorias</p>
            </div>
            <div className="bg-white rounded-lg p-3 text-center">
              <p className="text-lg font-bold text-emerald-600">{result.rag_atualizado ? "Sim" : "Não"}</p>
              <p className="text-xs text-gray-500">RAG Atualizado</p>
            </div>
            <div className="bg-white rounded-lg p-3 text-center col-span-1">
              <p className="text-xs text-gray-600 leading-relaxed">{result.mensagem}</p>
            </div>
          </div>
          {result.categorias_encontradas.length > 0 && (
            <div className="mt-3">
              <p className="text-xs text-gray-600 mb-1">Categorias encontradas:</p>
              <div className="flex flex-wrap gap-1">
                {result.categorias_encontradas.map((cat) => (
                  <span key={cat} className="text-xs bg-white px-2 py-0.5 rounded-full text-gray-700">{cat}</span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      <div className="card mt-6">
        <h3 className="text-sm font-semibold text-gray-700 mb-3">Formato Esperado</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="text-left text-gray-500 border-b">
                <th className="pb-2 pr-4">Coluna</th>
                <th className="pb-2 pr-4">Obrigatório</th>
                <th className="pb-2">Descrição</th>
              </tr>
            </thead>
            <tbody className="text-gray-700">
              <tr className="border-b"><td className="py-2 pr-4 font-mono">texto / Document / Ticket Description</td><td className="py-2 pr-4 text-green-600 font-medium">Sim</td><td className="py-2">Texto do ticket</td></tr>
              <tr className="border-b"><td className="py-2 pr-4 font-mono">resolucao / Resolution</td><td className="py-2 pr-4 text-gray-400">Não</td><td className="py-2">Resolução aplicada</td></tr>
              <tr><td className="py-2 pr-4 font-mono">categoria / Topic_group / Ticket Type</td><td className="py-2 pr-4 text-gray-400">Não</td><td className="py-2">Categoria do ticket</td></tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
