import React, { useEffect, useRef } from 'react';
import { ForceGraph2D } from 'react-force-graph';
import styled from 'styled-components';

interface SchemaNode {
  id: string;
  name: string;
  type: 'table' | 'column';
  columnType?: string;
}

interface SchemaLink {
  source: string;
  target: string;
  type: 'foreign_key' | 'relationship';
}

interface SchemaData {
  nodes: SchemaNode[];
  links: SchemaLink[];
}

const GraphContainer = styled.div`
  width: 100%;
  height: 600px;
  border: 1px solid ${props => props.theme.colors.border};
  border-radius: 4px;
`;

export const SchemaVisualizer: React.FC<{data: SchemaData}> = ({ data }) => {
  const graphRef = useRef();
  
  useEffect(() => {
    // Initial zoom to fit
    graphRef.current?.zoomToFit(400);
  }, [data]);
  
  return (
    <GraphContainer>
      <ForceGraph2D
        ref={graphRef}
        graphData={data}
        nodeAutoColorBy="type"
        nodeLabel={node => `${node.name} (${node.type})`}
        linkDirectionalArrowLength={4}
        linkDirectionalArrowRelPos={1}
        linkCurvature={0.25}
        onNodeClick={node => {
          // Handle node click - show details
        }}
      />
    </GraphContainer>
  );
};