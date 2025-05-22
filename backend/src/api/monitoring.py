from flask import Blueprint, jsonify
from datetime import datetime, timedelta
from services.monitor_service import MonitorService

monitor_bp = Blueprint('monitor', __name__)
monitor_service = MonitorService()

@monitor_bp.route('/stats/queries', methods=['GET'])
def get_query_stats():
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(hours=24)
    
    stats = monitor_service.get_query_stats(start_time, end_time)
    return jsonify(stats)

@monitor_bp.route('/stats/performance', methods=['GET'])
def get_performance_stats():
    stats = monitor_service.get_performance_stats()
    return jsonify(stats)

@monitor_bp.route('/stats/errors', methods=['GET'])
def get_error_stats():
    stats = monitor_service.get_error_stats()
    return jsonify(stats)

@monitor_bp.route('/stats/databases', methods=['GET'])
def get_database_stats():
    stats = monitor_service.get_database_stats()
    return jsonify(stats)