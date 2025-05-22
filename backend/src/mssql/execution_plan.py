from typing import Dict, List
import xml.etree.ElementTree as ET

class ExecutionPlanAnalyzer:
    def __init__(self):
        self.cost_threshold = 0.1  # 10% of batch cost
        
    def analyze(self, query: str) -> Dict:
        """Execution plan analizi yapar."""
        plan_xml = self._get_execution_plan(query)
        plan_tree = ET.fromstring(plan_xml)
        
        return {
            'cost_analysis': self._analyze_costs(plan_tree),
            'operations': self._analyze_operations(plan_tree),
            'warnings': self._analyze_warnings(plan_tree),
            'recommendations': self._generate_recommendations(plan_tree)
        }
        
    def _analyze_costs(self, plan_tree: ET.Element) -> Dict:
        """Maliyet analizi yapar."""
        costs = {
            'total_cost': 0,
            'cpu_cost': 0,
            'io_cost': 0,
            'subtree_costs': []
        }
        
        for node in plan_tree.findall(".//StmtSimple"):
            costs['total_cost'] += float(node.get('StatementSubTreeCost', 0))
            
        for node in plan_tree.findall(".//RelOp"):
            cpu_cost = float(node.get('EstimatedCPUCost', 0))
            io_cost = float(node.get('EstimatedIOCost', 0))
            
            costs['cpu_cost'] += cpu_cost
            costs['io_cost'] += io_cost
            
            subtree_cost = float(node.get('EstimatedTotalSubtreeCost', 0))
            if subtree_cost > self.cost_threshold * costs['total_cost']:
                costs['subtree_costs'].append({
                    'operation': node.get('PhysicalOp'),
                    'cost': subtree_cost,
                    'details': self._get_operation_details(node)
                })
                
        return costs
        
    def _analyze_operations(self, plan_tree: ET.Element) -> List[Dict]:
        """Operasyon analizi yapar."""
        operations = []
        
        for node in plan_tree.findall(".//RelOp"):
            operation = {
                'type': node.get('PhysicalOp'),
                'logical_op': node.get('LogicalOp'),
                'estimated_rows': float(node.get('EstimateRows', 0)),
                'estimated_cost': float(node.get('EstimatedTotalSubtreeCost', 0)),
                'parallel': node.get('Parallel') == 'true',
                'details': self._get_operation_details(node)
            }
            
            operations.append(operation)
            
        return operations