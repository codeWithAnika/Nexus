import { useEffect, useMemo, useRef } from 'react'
import CytoscapeComponent from 'react-cytoscapejs'
import cytoscape from 'cytoscape'
import { entityColor, riskColor } from '../../utils/entityVisuals'

export default function NetworkGraph({
  typeFilter,
  riskFilter,
  selectedId,
  onSelect,
  highlightPath, // { path: [ids], edges: [edge] } | null
  searchTerm,
  graphData,
}) {
  const cyRef = useRef(null)

  const visibleEntities = useMemo(
    () =>
      (graphData?.nodes || []).filter(
        (e) =>
          (typeFilter.length === 0 || typeFilter.includes(e.type)) &&
          (riskFilter.length === 0 || riskFilter.includes(e.riskLevel))
      ),
    [typeFilter, riskFilter, graphData]
  )
  const visibleIds = useMemo(() => new Set(visibleEntities.map((e) => e.id)), [visibleEntities])
  const visibleRelationships = useMemo(
    () => (graphData?.edges || []).filter((r) => visibleIds.has(r.source) && visibleIds.has(r.target)),
    [graphData, visibleIds]
  )

  const elements = useMemo(
    () => [
      ...visibleEntities.map((e) => ({
        data: { id: e.id, label: e.name, type: e.type, risk: e.riskLevel },
      })),
      ...visibleRelationships.map((r) => ({
        data: { id: r.id, source: r.source, target: r.target, label: r.type },
      })),
    ],
    [visibleEntities, visibleRelationships]
  )

  const stylesheet = useMemo(
    () => [
      {
        selector: 'node',
        style: {
          'background-color': (n) => entityColor(n.data('type')),
          label: 'data(label)',
          'font-size': 9,
          color: '#aab4c7',
          'text-valign': 'bottom',
          'text-margin-y': 6,
          width: 30,
          height: 30,
          'border-width': 2,
          'border-color': (n) => riskColor(n.data('risk')),
          'transition-property': 'opacity, border-width',
          'transition-duration': 150,
        },
      },
      {
        selector: 'edge',
        style: {
          width: 1.4,
          'line-color': '#2a3650',
          'target-arrow-color': '#2a3650',
          'target-arrow-shape': 'triangle',
          'arrow-scale': 0.7,
          'curve-style': 'bezier',
          opacity: 0.65,
        },
      },
      {
        selector: '.dim',
        style: { opacity: 0.12 },
      },
      {
        selector: '.selected',
        style: {
          'border-width': 4,
          'border-color': '#3aa8ff',
          width: 38,
          height: 38,
        },
      },
      {
        selector: '.neighbor',
        style: { 'border-width': 3 },
      },
      {
        selector: '.path-node',
        style: {
          'border-width': 4,
          'border-color': '#3ecf8e',
          width: 36,
          height: 36,
        },
      },
      {
        selector: '.path-edge',
        style: {
          'line-color': '#3ecf8e',
          'target-arrow-color': '#3ecf8e',
          width: 3,
          opacity: 1,
        },
      },
      {
        selector: '.search-match',
        style: {
          'border-width': 4,
          'border-color': '#e8a13a',
        },
      },
    ],
    []
  )

  // selection + neighbor highlighting
  useEffect(() => {
    const cy = cyRef.current
    if (!cy) return
    cy.elements().removeClass('dim selected neighbor path-node path-edge search-match')

    if (highlightPath?.path?.length) {
      const pathNodeIds = new Set(highlightPath.path)
      const pathEdgeIds = new Set(highlightPath.edges.map((e) => e.id))
      cy.nodes().forEach((n) => {
        if (pathNodeIds.has(n.id())) n.addClass('path-node')
        else n.addClass('dim')
      })
      cy.edges().forEach((e) => {
        if (pathEdgeIds.has(e.id())) e.addClass('path-edge')
        else e.addClass('dim')
      })
      return
    }

    if (selectedId) {
      const node = cy.getElementById(selectedId)
      if (node && node.length) {
        const neighborhood = node.closedNeighborhood()
        cy.elements().addClass('dim')
        neighborhood.removeClass('dim')
        node.removeClass('dim').addClass('selected')
        neighborhood.nodes().not(node).addClass('neighbor')
      }
    }

    if (searchTerm) {
      cy.nodes().forEach((n) => {
        if (n.data('label').toLowerCase().includes(searchTerm.toLowerCase())) {
          n.addClass('search-match').removeClass('dim')
        }
      })
    }
  }, [selectedId, highlightPath, searchTerm, elements])

  return (
    <CytoscapeComponent
      elements={CytoscapeComponent.normalizeElementsArray(elements)}
      style={{ width: '100%', height: '100%' }}
      stylesheet={stylesheet}
      layout={{ name: 'cose', animate: false, padding: 40, nodeRepulsion: 9000, idealEdgeLength: 90 }}
      cy={(cy) => {
        cyRef.current = cy
        cy.off('tap', 'node')
        cy.on('tap', 'node', (evt) => onSelect(evt.target.id()))
        cy.off('tap')
        cy.on('tap', (evt) => {
          if (evt.target === cy) onSelect(null)
        })
      }}
    />
  )
}

export function fitAndReset(cy) {
  if (!cy) return
  cy.elements().removeClass('dim selected neighbor path-node path-edge search-match')
  cy.fit(undefined, 40)
}

cytoscape // keep import referenced for future layout extensions
