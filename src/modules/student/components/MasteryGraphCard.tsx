import { useEffect, useRef, useState } from 'react'
import * as d3 from 'd3'
import {
  Card, CardContent, Typography, Box, Chip, CircularProgress, Alert,
} from '@mui/material'
import { useQuery } from '@tanstack/react-query'
import { container } from '../../../di/container'
import type { ConceptNode, ConceptEdge, StudentProfile } from '../../../types/domain'

interface Props {
  student: StudentProfile
  module: string
}

type D3Node = ConceptNode & d3.SimulationNodeDatum & { topic_group: number }
type D3Link = Omit<ConceptEdge, 'source' | 'target'> & d3.SimulationLinkDatum<D3Node>

function nodeColor(mastery: number) {
  if (mastery >= 0.90) return { f: '#5DCAA5', s: '#0F6E56', t: '#085041' }
  if (mastery >= 0.75) return { f: '#E1F5EE', s: '#1D9E75', t: '#085041' }
  if (mastery >= 0.60) return { f: '#FAEEDA', s: '#BA7517', t: '#633806' }
  return { f: '#FCEBEB', s: '#E24B4A', t: '#791F1F' }
}

function masteryLabel(m: number) {
  if (m >= 0.90) return 'Mastered'
  if (m >= 0.75) return 'Proficient'
  if (m >= 0.60) return 'Developing'
  return 'Needs support'
}

const R = 24

export function MasteryGraphCard({ student, module }: Props) {
  const svgRef       = useRef<SVGSVGElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)
  const simRef       = useRef<d3.Simulation<D3Node, D3Link> | null>(null)
  const [selectedNode, setSelectedNode] = useState<ConceptNode | null>(null)

  const { data: graph, isLoading } = useQuery({
    queryKey: ['mastery', student.id_student, module, student.assessments?.length ?? 0],
    queryFn: () => container.masteryService.getConceptGraph(
      student.id_student, module, student.assessments ?? [],
    ),
    enabled: !!module,
  })

  useEffect(() => {
    if (!graph || !svgRef.current || !containerRef.current) return

    const W = containerRef.current.clientWidth || 640
    const H = 320
    const groupX: Record<number, number> = { 1: W * 0.18, 2: W * 0.5, 3: W * 0.82 }

    const nodes: D3Node[] = graph.nodes.map((n) => ({
      ...n,
      x: groupX[n.topic_group] + (Math.random() - 0.5) * 50,
      y: H / 2 + (Math.random() - 0.5) * 80,
    }))
    const edges: D3Link[] = graph.edges.map((e) => ({ ...e }))

    const svg = d3.select(svgRef.current)
    svg.selectAll('*').remove()
    svg.attr('viewBox', `0 0 ${W} ${H}`).attr('width', '100%').attr('height', H)

    svg.append('defs').append('marker')
      .attr('id', 'marr-card').attr('viewBox', '0 0 10 10').attr('refX', 8).attr('refY', 5)
      .attr('markerWidth', 5).attr('markerHeight', 5).attr('orient', 'auto-start-reverse')
      .append('path').attr('d', 'M2 1L8 5L2 9').attr('fill', 'none').attr('stroke', '#B4B2A9')
      .attr('stroke-width', 1.5).attr('stroke-linecap', 'round').attr('stroke-linejoin', 'round')

    const linkSel = svg.append('g').selectAll('line').data(edges).join('line')
      .attr('stroke', '#D3D1C7').attr('stroke-width', 1).attr('marker-end', 'url(#marr-card)')

    const nodeSel = svg.append('g').selectAll<SVGGElement, D3Node>('g').data(nodes).join('g')
      .attr('cursor', 'pointer')
      .on('click', (_, d) => setSelectedNode((prev) => prev?.id === d.id ? null : d))
      .call(
        d3.drag<SVGGElement, D3Node>()
          .on('start', (e, d) => { if (!e.active) simRef.current?.alphaTarget(0.3).restart(); d.fx = d.x; d.fy = d.y })
          .on('drag',  (e, d) => { d.fx = e.x; d.fy = e.y })
          .on('end',   (e, d) => { if (!e.active) simRef.current?.alphaTarget(0); d.fx = null; d.fy = null })
      )

    nodeSel.append('circle').attr('r', R)
      .attr('fill',   (d) => nodeColor(d.mastery).f)
      .attr('stroke', (d) => nodeColor(d.mastery).s)
      .attr('stroke-width', 2)

    nodeSel.append('text')
      .text((d) => `${Math.round(d.mastery * 100)}%`)
      .attr('text-anchor', 'middle').attr('dominant-baseline', 'central').attr('y', 0.5)
      .attr('font-size', 11).attr('font-weight', 500)
      .attr('fill', (d) => nodeColor(d.mastery).t).attr('pointer-events', 'none')

    nodeSel.append('text')
      .text((d) => d.label)
      .attr('text-anchor', 'middle').attr('y', R + 13).attr('font-size', 11)
      .attr('fill', '#888780').attr('pointer-events', 'none')

    const sim = d3.forceSimulation<D3Node>(nodes)
      .force('link',    d3.forceLink<D3Node, D3Link>(edges).id((d) => d.id).distance(95).strength(0.55))
      .force('charge',  d3.forceManyBody().strength(-270))
      .force('center',  d3.forceCenter(W / 2, H / 2 - 10))
      .force('collide', d3.forceCollide(R + 22))
      .force('x',       d3.forceX((d: D3Node) => groupX[d.topic_group]).strength(0.32))

    simRef.current = sim

    sim.on('tick', () => {
      linkSel
        .attr('x1', (d) => (d.source as D3Node).x!)
        .attr('y1', (d) => (d.source as D3Node).y!)
        .attr('x2', (d) => {
          const dx = (d.target as D3Node).x! - (d.source as D3Node).x!
          const dy = (d.target as D3Node).y! - (d.source as D3Node).y!
          const l  = Math.sqrt(dx * dx + dy * dy) || 1
          return (d.target as D3Node).x! - (dx / l) * (R + 9)
        })
        .attr('y2', (d) => {
          const dx = (d.target as D3Node).x! - (d.source as D3Node).x!
          const dy = (d.target as D3Node).y! - (d.source as D3Node).y!
          const l  = Math.sqrt(dx * dx + dy * dy) || 1
          return (d.target as D3Node).y! - (dy / l) * (R + 9)
        })

      nodeSel.attr('transform', (d) =>
        `translate(${Math.max(R + 4, Math.min(W - R - 4, d.x!))},${Math.max(R + 28, Math.min(H - R - 20, d.y!))})`)
    })

    return () => { sim.stop() }
  }, [graph])

  return (
    <Card elevation={0} sx={{ borderRadius: 2, border: '1px solid #E5E3DC' }}>
      <CardContent>
        <Typography sx={{ fontSize: 12, fontWeight: 500, color: '#0A1628', mb: 1.5 }}>
          Concept mastery
        </Typography>

        <Box sx={{ display: 'flex', gap: 1, mb: 1.5, flexWrap: 'wrap' }}>
          {[
            { label: 'Mastered ≥90%',  bg: '#5DCAA5', color: '#085041' },
            { label: 'Proficient ≥75%', bg: '#E1F5EE', color: '#085041' },
            { label: 'Developing ≥60%', bg: '#FAEEDA', color: '#633806' },
            { label: 'Needs support',   bg: '#FCEBEB', color: '#791F1F' },
          ].map((l) => (
            <Chip key={l.label} label={l.label} size="small"
              sx={{ bgcolor: l.bg, color: l.color, fontSize: 11, fontFamily: '"IBM Plex Mono", monospace', height: 22 }}
            />
          ))}
        </Box>

        {isLoading && (
          <Box sx={{ display: 'flex', gap: 1.5, alignItems: 'center', py: 4, justifyContent: 'center' }}>
            <CircularProgress size={18} sx={{ color: '#1D9E75' }} />
            <Typography sx={{ fontSize: 13, color: '#6B7280', fontFamily: '"IBM Plex Mono", monospace' }}>
              Building concept graph…
            </Typography>
          </Box>
        )}

        <div ref={containerRef}>
          <svg ref={svgRef} style={{ display: graph ? 'block' : 'none' }} />
        </div>

        {selectedNode && (
          <Box sx={{ mt: 1.5, pt: 1.5, borderTop: '1px solid #F0EFE9', display: 'flex', alignItems: 'center', gap: 2, flexWrap: 'wrap' }}>
            <Box sx={{ flex: 1 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 0.5 }}>
                <Typography sx={{ fontSize: 13, fontWeight: 500, color: '#0A1628' }}>{selectedNode.label}</Typography>
                <Chip
                  label={masteryLabel(selectedNode.mastery)}
                  size="small"
                  sx={{ bgcolor: nodeColor(selectedNode.mastery).f, color: nodeColor(selectedNode.mastery).t, fontFamily: '"IBM Plex Mono", monospace', fontSize: 11, height: 20 }}
                />
              </Box>
              <Typography sx={{ fontSize: 20, fontWeight: 600, fontFamily: '"IBM Plex Mono", monospace', color: nodeColor(selectedNode.mastery).s }}>
                {Math.round(selectedNode.mastery * 100)}%
              </Typography>
            </Box>
            <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 1.5 }}>
              <Box>
                <Typography sx={{ fontSize: 11, color: '#9CA3AF', fontFamily: '"IBM Plex Mono", monospace', mb: 0.25 }}>Evidence</Typography>
                <Typography sx={{ fontSize: 12, fontWeight: 500, fontFamily: '"IBM Plex Mono", monospace', color: '#0A1628' }}>{selectedNode.evidence_count} assessments</Typography>
              </Box>
              <Box>
                <Typography sx={{ fontSize: 11, color: '#9CA3AF', fontFamily: '"IBM Plex Mono", monospace', mb: 0.25 }}>Confidence</Typography>
                <Typography sx={{ fontSize: 12, fontWeight: 500, fontFamily: '"IBM Plex Mono", monospace', color: '#0A1628' }}>{Math.round(selectedNode.confidence * 100)}%</Typography>
              </Box>
              <Box>
                <Typography sx={{ fontSize: 11, color: '#9CA3AF', fontFamily: '"IBM Plex Mono", monospace', mb: 0.25 }}>Prerequisites</Typography>
                <Typography sx={{ fontSize: 11, color: '#6B7280' }}>
                  {graph?.edges.filter((e) => e.target === selectedNode.id).map((e) => graph.nodes.find((n) => n.id === e.source)?.label).join(', ') || 'None'}
                </Typography>
              </Box>
              <Box>
                <Typography sx={{ fontSize: 11, color: '#9CA3AF', fontFamily: '"IBM Plex Mono", monospace', mb: 0.25 }}>Unlocks</Typography>
                <Typography sx={{ fontSize: 11, color: '#6B7280' }}>
                  {graph?.edges.filter((e) => e.source === selectedNode.id).map((e) => graph.nodes.find((n) => n.id === e.target)?.label).join(', ') || 'None'}
                </Typography>
              </Box>
            </Box>
          </Box>
        )}

        <Alert severity="info" icon={false} sx={{ mt: 1.5, borderRadius: 1.5, fontSize: 11, fontFamily: '"IBM Plex Mono", monospace', py: 0.25 }}>
          Mock data — concept nodes sourced from G_course (Neo4j) in deployment
        </Alert>
      </CardContent>
    </Card>
  )
}
