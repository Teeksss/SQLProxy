#!/bin/bash

# Redis service yönetimi
function check_redis() {
    echo "Checking Redis service..."
    if docker ps | grep -q sqlproxy_redis; then
        echo "Redis container is running"
        return 0
    else
        echo "Redis container is not running"
        return 1
    fi
}

function start_redis() {
    echo "Starting Redis service..."
    docker-compose up -d redis
    
    # Wait for healthcheck
    echo "Waiting for Redis to be ready..."
    for i in {1..30}; do
        if docker-compose exec redis redis-cli ping > /dev/null 2>&1; then
            echo "Redis is ready"
            return 0
        fi
        sleep 1
    done
    
    echo "Redis failed to start"
    return 1
}

function stop_redis() {
    echo "Stopping Redis service..."
    docker-compose stop redis
}

function restart_redis() {
    echo "Restarting Redis service..."
    stop_redis
    start_redis
}

# Main logic
case "$1" in
    start)
        start_redis
        ;;
    stop)
        stop_redis
        ;;
    restart)
        restart_redis
        ;;
    status)
        check_redis
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status}"
        exit 1
        ;;
esac