import { PipelineTable } from '@/components/PipelineTable'

export default function PipelinePage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Pipeline</h1>
        <p className="text-gray-500 text-sm mt-1">Deals abertos ordenados por score de prioridade</p>
      </div>
      <PipelineTable />
    </div>
  )
}
