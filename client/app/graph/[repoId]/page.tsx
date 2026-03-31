'use client'

import { useEffect, useState, useCallback, memo } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { ArrowLeft, Download } from 'lucide-react'
import Link from 'next/link'
import ReactFlow, {
  Background,
  Controls,
  useNodesState,
  useEdgesState,
  Node,
  Edge,
  Handle,
  Position,
} from 'reactflow'
import 'reactflow/dist/style.css'
import { Button } from '@/components/ui/button'
import { Separator } from '@/components/ui/separator'
import { Logo } from '@/components/shared/Logo'
import { LoadingSpinner } from '@/components/shared/LoadingSpinner'
import { ErrorState } from '@/components/shared/ErrorState'
import { getRepository } from '@/lib/api/repos'
import { getDependencyGraph } from '@/lib/api/analysis'
import type { Repository } from '@/lib/types'


const FileNode = memo(({ data }: { data: { label: string; type: string } }) => (
  <div className="text-xs text-white">
    <Handle type="target" position={Position.Top} />
    <div className="font-semibold truncate max-w-[130px]">{data.label}</div>
    <div className="opacity-70">{data.type}</div>
    <Handle type="source" position={Position.Bottom} />
  </div>
))
FileNode.displayName = 'FileNode'

const nodeTypes = { fileNode: FileNode }

export default function GraphPage() {
  const params = useParams()
  const repoId = params.repoId as string

  const [repository, setRepository] = useState<Repository | null>(null)
  const [nodes, setNodes, onNodesChange] = useNodesState([])
  const [edges, setEdges, onEdgesChange] = useEdgesState([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [edgeCount, setEdgeCount] = useState(0)

  useEffect(() => {
    const fetchData = async () => {
      try {
        setIsLoading(true)
        const [repo, graph] = await Promise.all([
          getRepository(repoId),
          getDependencyGraph(repoId),
        ])
        setRepository(repo)

        console.log('Graph data received:', graph)
        console.log('Nodes count:', graph?.nodes?.length)
        console.log('Edges count:', graph?.edges?.length)

        if (graph && graph.nodes) {
          const gridCols = Math.ceil(Math.sqrt(graph.nodes.length))
          const spacing = 200

          const graphNodes: Node[] = graph.nodes.map((node, index) => {
            const row = Math.floor(index / gridCols)
            const col = index % gridCols

            return {
              id: node.id,
              type: 'fileNode', 
              data: {
                label: node.label,
                type: node.type,
              },
              position: { x: col * spacing, y: row * spacing },
              style: {
                background: node.type === 'file' ? '#3B82F6' : '#8B5CF6',
                border: '1px solid rgba(255,255,255,0.2)',
                borderRadius: '8px',
                padding: '10px',
                width: 150,
              },
            }
          })

          const graphEdges: Edge[] = (graph.edges || []).map((edge, index) => ({
            id: `${edge.source}-${edge.target}-${index}`,
            source: edge.source,
            target: edge.target,
            animated: true,
            style: { stroke: '#64748b', strokeWidth: 2 },
          }))

          setNodes(graphNodes)
          setEdges(graphEdges)
          setEdgeCount(graphEdges.length)

          console.log('Set nodes:', graphNodes.length)
          console.log('Set edges:', graphEdges.length)
        }
      } catch (err) {
        console.error('Failed to fetch data:', err)
        setError(err instanceof Error ? err.message : 'Failed to load graph')
      } finally {
        setIsLoading(false)
      }
    }

    fetchData()
  }, [repoId, setNodes, setEdges])

  const handleDownload = useCallback(() => {
    console.log('Download graph')
    // TODO: Implement export
  }, [])

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <LoadingSpinner size="lg" text="Loading dependency graph..." />
      </div>
    )
  }

  if (error || !repository) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <ErrorState
          title="Failed to load graph"
          message={error || 'Repository not found'}
          onRetry={() => window.location.reload()}
        />
      </div>
    )
  }

  return (
    <div style={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <header className="border-b border-border/40 backdrop-blur-sm z-50 bg-background/80 flex-shrink-0">
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
              <p className="text-xs text-muted-foreground">Dependency Graph</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {edgeCount < 10 && nodes.length > 20 && (
              <span className="text-xs text-yellow-500 mr-2">
                ⚠️ Only {edgeCount} edges detected — backend may be missing dependencies
              </span>
            )}
            <Button variant="ghost" size="sm" onClick={handleDownload} className="gap-2">
              <Download className="h-4 w-4" />
              Export
            </Button>
          </div>
        </div>
      </header>

      {/* Graph */}
      <div style={{ flex: 1, position: 'relative' }}>
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          nodeTypes={nodeTypes} 
          fitView
          style={{ width: '100%', height: '100%' }}
          className="bg-background"
        >
          <Background />
          <Controls />
        </ReactFlow>

        {/* Legend */}
        <div className="absolute bottom-4 left-4 bg-card border border-border rounded-lg p-4 shadow-lg space-y-2">
          <h3 className="text-sm font-semibold mb-2">Legend</h3>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded bg-[#3B82F6]" />
            <span className="text-xs">File</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded bg-[#8B5CF6]" />
            <span className="text-xs">Module</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-8 h-0.5 bg-[#64748b]" />
            <span className="text-xs">Dependency</span>
          </div>
        </div>
      </div>
    </div>
  )
}
