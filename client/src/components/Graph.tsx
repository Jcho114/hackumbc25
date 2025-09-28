import { useState, useCallback, useEffect } from "react";
import {
  ReactFlow,
  type Node,
  type Edge,
  applyNodeChanges,
  applyEdgeChanges,
  useNodesState,
  useEdgesState,
  ConnectionLineType,
} from "@xyflow/react";
import type { SessionEdge, SessionMetadata, SessionNode } from "@/api/sessions";
import dagre from "@dagrejs/dagre";
import GraphSessionNode from "@/components/GraphSessionNode";
import "@xyflow/react/dist/style.css";

interface GraphProps {
  metadata: SessionMetadata;
}

function toGraphNodes(nodes: SessionNode[]) {
  return nodes.map((node: SessionNode) => {
    return {
      id: node.node_id,
      position: { x: Math.random() * 1000, y: Math.random() * 800 },
      type: "graphSessionNode",
      data: {
        label: node.node_id,
        columns: node.columns || [],
      },
    };
  });
}

function toGraphEdges(edges: SessionEdge[]) {
  return edges.map((edge) => ({
    id: `${edge.src_id}-${edge.dst_id}`,
    source: edge.src_id,
    target: edge.dst_id,
    label: edge.operation,
    labelBgStyle: { fill: "#f9fafb" },
    markerEnd: {
      type: "arrowclosed",
      color: "black",
    },
    labelStyle: {
      fontSize: 12,
      fontWeight: 500,
      fill: "#000",
    },
  }));
}

const dagreGraph = new dagre.graphlib.Graph().setDefaultEdgeLabel(() => ({}));
const nodeWidth = 300;
const nodeHeight = 36;

export const getLayoutedElements = (
  metadata: SessionMetadata,
  direction = "LR"
) => {
  const nodes = toGraphNodes(metadata.nodes);
  const edges = toGraphEdges(metadata.edges);
  const isHorizontal = direction === "LR";
  dagreGraph.setGraph({ rankdir: direction });

  nodes.forEach((node) => {
    dagreGraph.setNode(node.id, { width: nodeWidth, height: nodeHeight });
  });

  edges.forEach((edge) => {
    dagreGraph.setEdge(edge.source, edge.target);
  });

  dagre.layout(dagreGraph);

  const newNodes = nodes.map((node) => {
    const nodeWithPosition = dagreGraph.node(node.id);
    const newNode = {
      ...node,
      targetPosition: isHorizontal ? "left" : "top",
      sourcePosition: isHorizontal ? "right" : "bottom",
      position: {
        x: nodeWithPosition.x - nodeWidth / 2,
        y: nodeWithPosition.y - nodeHeight / 2,
      },
    };

    return newNode;
  });

  return { nodes: newNodes, edges };
};

const nodeTypes = {
  graphSessionNode: GraphSessionNode,
};

const Graph = ({ metadata }: GraphProps) => {
  const [nodes, setNodes, onNodesChange] = useNodesState<Node>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([]);

  useEffect(() => {
    const { nodes, edges } = getLayoutedElements(metadata);
    setNodes(nodes);
    setEdges(edges);
  }, [metadata]);

  return (
    <div className="absolute w-full h-full justify-center items-center">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        connectionLineType={ConnectionLineType.SmoothStep}
        minZoom={0.1}
        nodesDraggable={false}
        nodesConnectable={false}
        edgesFocusable={false}
        fitView
      />
    </div>
  );
};

export default Graph;
