'use client'

import { useEffect, useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { ArrowLeft, Download } from 'lucide-react'
import Link from 'next/link'
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  Node,
  Edge,
  MarkerType,
} from 'reactflow'
import 'reactflow/dist/style.css'
import { Button } from '@/components/ui/button'
import { Separator } from '@/components/ui/separator'
import { Logo } from '@/components/shared/Logo'
import { LoadingSpinner } from '@/components/shared/LoadingSpinner'
import { ErrorState } from '@/components/shared/ErrorState'
import { getRepository } from '@/lib/api/repos'
import { getExecutionFlows } from '@/lib/api/analysis'
import type { Repository, ExecutionFlow } from '@/lib/types'

export default function FlowPage() {
  const params = useParams()
  const router = useRouter()
  const repoId = params.repoId as string

  const [repository, setRepository] = useState<Repository | null>(null)
  const [nodes, setNodes, onNodesChange] = useNodesState([])
  const [edges, setEdges, onEdgesChange] = useEdgesState([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchData = async () => {
      try {
        setIsLoading(true)
        const [repo, flows] = await Promise.all([
          getRepository(repoId),
          getExecutionFlows(repoId),
        ])
        setRepository(repo)

        if (flows && flows.length > 0) {
          // Use the first execution flow
          const flow = flows[0]

          const flowNodes: Node[] = flow.nodes.map((node, index) => ({
            id: node.id,
            type: node.type === 'start' || node.type === 'end' ? 'default' : 'default',
            data: {
              label: (
                <div className="text-xs">
                  <div className="font-semibold">{node.label}</div>
                  {node.description && (
                    <div className="text-muted-foreground text-[10px]">{node.description}</div>
                  )}
                </div>
              ),
            },
            position: { x: 250, y: index * 120 },
            style: {
              background:
                node.type === 'start'
                  ? '#10B981'
                  : node.type === 'end'
                  ? '#EF4444'
                  : node.type === 'decision'
                  ? '#F59E0B'
                  : '#3B82F6',
              color: 'white',
              border: '2px solid rgba(255,255,255,0.2)',
              borderRadius: node.type === 'decision' ? '4px' : '8px',
              padding: '12px',
              minWidth: '150px',
            },
          }))

          const flowEdges: Edge[] = flow.edges.map((edge, index) => ({
            id: `${edge.source}-${edge.target}-${index}`,
            source: edge.source,
            target: edge.target,
            type: 'smoothstep',
            animated: true,
            style: { stroke: '#64748b', strokeWidth: 2 },
            label: edge.label,
            markerEnd: {
              type: MarkerType.ArrowClosed,
              color: '#64748b',
            },
          }))

          setNodes(flowNodes)
          setEdges(flowEdges)
        }
      } catch (err) {
        console.error('Failed to fetch data:', err)
        setError(err instanceof Error ? err.message : 'Failed to load flow')
      } finally {
        setIsLoading(false)
      }
    }

    fetchData()
  }, [repoId, setNodes, setEdges])

  const handleDownload = () => {
    // TODO: Implement flow export functionality
    console.log('Download flow')
  }

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <LoadingSpinner size="lg" text="Loading execution flow..." />
      </div>
    )
  }

  if (error || !repository) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <ErrorState
          title="Failed to load flow"
          message={error || 'Repository not found'}
          onRetry={() => window.location.reload()}
        />
      </div>
    )
  }

  return (
    <div className="flex min-h-screen flex-col">
      {/* Header */}
      <header className="border-b border-border/40 backdrop-blur-sm z-50 bg-background/80">
        <div className="container flex h-14 items-center justify-between px-4 mx-auto">
          <div className="flex items-center gap-4">
            <Link href={`/chat/${repoId}`}>
              <Button variant="ghost" size="icon">
                <ArrowLeft className="h-4 w-4" />
              </Button>
            </Link>
            <Separator orientation="vertical" className="h-6" />
            <Logo showText={false} href="/" />
            <div className="flex flex-col">
              <h1 className="text-sm font-semibold">{repository.name}</h1>
              <p className="text-xs text-muted-foreground">Execution Flow</p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <Button variant="ghost" size="sm" onClick={handleDownload} className="gap-2">
              <Download className="h-4 w-4" />
              Export
            </Button>
          </div>
        </div>
      </header>

      {/* Flow Visualization */}
      <div className="flex-1 relative">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          fitView
          className="bg-background"
        >
          <Background />
          <Controls />
          <MiniMap
            nodeColor={(node) => {
              return node.style?.background as string || '#3B82F6'
            }}
            maskColor="rgba(0, 0, 0, 0.3)"
          />
        </ReactFlow>

        {/* Legend */}
        <div className="absolute bottom-4 left-4 bg-card border border-border rounded-lg p-4 shadow-lg space-y-2">
          <h3 className="text-sm font-semibold mb-2">Legend</h3>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded bg-[#10B981]" />
            <span className="text-xs">Entry Point</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded bg-[#3B82F6]" />
            <span className="text-xs">Process</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 bg-[#F59E0B]" />
            <span className="text-xs">Decision</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded bg-[#EF4444]" />
            <span className="text-xs">Exit Point</span>
          </div>
        </div>
      </div>
    </div>
  )
}
