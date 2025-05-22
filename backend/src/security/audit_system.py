from typing import Dict, List, Optional
from datetime import datetime
import elasticsearch
from .enhanced_security import SecurityManager

class AuditSystem:
    def __init__(self):
        self.es = elasticsearch.Elasticsearch(['http://localhost:9200'])
        self.security_manager = SecurityManager()
        
    def log_event(self, event_type: str, data: Dict):
        event = {
            'timestamp': datetime.utcnow(),
            'event_type': event_type,
            'data': self.security_manager.encrypt_sensitive_data(data)
        }
        
        self.es.index(
            index='sqlproxy-audit',
            document=event
        )
        
    def get_user_activity(self, user_id: int, 
                         start_date: datetime,
                         end_date: datetime) -> List[Dict]:
        query = {
            'query': {
                'bool': {
                    'must': [
                        {'term': {'data.user_id': user_id}},
                        {
                            'range': {
                                'timestamp': {
                                    'gte': start_date,
                                    'lte': end_date
                                }
                            }
                        }
                    ]
                }
            }
        }
        
        result = self.es.search(
            index='sqlproxy-audit',
            body=query
        )
        
        return [hit['_source'] for hit in result['hits']['hits']]
        
    def analyze_security_events(self) -> Dict:
        # Analyze security events for patterns
        aggs_query = {
            'aggs': {
                'events_over_time': {
                    'date_histogram': {
                        'field': 'timestamp',
                        'interval': 'hour'
                    }
                },
                'event_types': {
                    'terms': {
                        'field': 'event_type'
                    }
                }
            }
        }
        
        result = self.es.search(
            index='sqlproxy-audit',
            body=aggs_query
        )
        
        return self._process_security_analytics(result)
        
    def _process_security_analytics(self, result: Dict) -> Dict:
        return {
            'events_timeline': self._process_timeline(
                result['aggregations']['events_over_time']
            ),
            'event_distribution': self._process_distribution(
                result['aggregations']['event_types']
            )
        }