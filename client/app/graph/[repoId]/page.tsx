'use client'

import { useEffect, useState, useCallback } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { ArrowLeft, Download, ZoomIn, ZoomOut, Maximize2 } from 'lucide-react'
import Link from 'next/link'
import ReactFlow, {
  Background,
  Controls,
  useNodesState,
  useEdgesState,
  Node,
  Edge,
} from 'reactflow'
import 'reactflow/dist/style.css'
import { Button } from '@/components/ui/button'
import { Separator } from '@/components/ui/separator'
import { Logo } from '@/components/shared/Logo'
import { LoadingSpinner } from '@/components/shared/LoadingSpinner'
import { ErrorState } from '@/components/shared/ErrorState'
import { getRepository } from '@/lib/api/repos'
import { getDependencyGraph } from '@/lib/api/analysis'
import type { Repository, DependencyGraph } from '@/lib/types'

export default function GraphPage() {
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
        const [repo, graph] = await Promise.all([
          getRepository(repoId),
          getDependencyGraph(repoId),
        ])
        setRepository(repo)

        console.log('Graph data received:', graph)
        console.log('Nodes count:', graph?.nodes?.length)
        console.log('Edges count:', graph?.edges?.length)

        if (graph && graph.nodes) {
          // Calculate grid layout for nodes
          const gridCols = Math.ceil(Math.sqrt(graph.nodes.length))
          const spacing = 200
          
          const graphNodes: Node[] = graph.nodes.map((node, index) => {
            const row = Math.floor(index / gridCols)
            const col = index % gridCols
            
            return {
              id: node.id,
              type: 'default',
              data: {
                label: (
                  <div className="text-xs">
                    <div className="font-semibold">{node.label}</div>
                    <div className="text-muted-foreground">{node.type}</div>
                  </div>
                ),
              },
              position: { x: col * spacing, y: row * spacing },
              style: {
                background: node.type === 'file' ? '#3B82F6' : '#8B5CF6',
                color: 'white',
                border: '1px solid #1E40AF',
                borderRadius: '8px',
                padding: '10px',
                width: 150,
              },
            }
          })

          const graphEdges: Edge[] = graph.edges.map((edge, index) => ({
            id: `${edge.source}-${edge.target}-${index}`,
            source: edge.source,
            target: edge.target,
            animated: true,
            style: { stroke: '#64748b', strokeWidth: 2 },
          }))

          setNodes(graphNodes)
          setEdges(graphEdges)
          
          console.log('Set nodes:', graphNodes.length)
          console.log('Set edges:', graphEdges.length)
          console.log('First node:', graphNodes[0])
          console.log('First edge:', graphEdges[0])
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

  console.log('Rendering with nodes:', nodes.length, 'edges:', edges.length)

  const handleDownload = () => {
    // TODO: Implement graph export functionality
    console.log('Download graph')
  }

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
    <div className="flex min-h-screen flex-col" style={{ height: '100vh' }}>
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
              <p className="text-xs text-muted-foreground">Dependency Graph</p>
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

      {/* Graph Visualization */}
      <div className="relative" style={{ width: '100%', height: 'calc(100vh - 3.5rem)' }}>
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
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
