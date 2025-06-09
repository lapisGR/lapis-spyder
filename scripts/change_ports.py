#!/usr/bin/env python3
"""
Port Configuration Script for Lapis Spider

This script helps you easily change all service ports by updating environment files.
"""

import os
import sys
from pathlib import Path


def update_env_file(file_path: Path, updates: dict):
    """Update environment file with new values."""
    if not file_path.exists():
        print(f"Creating {file_path}")
        file_path.parent.mkdir(parents=True, exist_ok=True)
        content = ""
    else:
        with open(file_path, 'r') as f:
            content = f.read()
    
    lines = content.split('\n') if content else []
    updated_keys = set()
    
    # Update existing lines
    for i, line in enumerate(lines):
        if '=' in line and not line.strip().startswith('#'):
            key = line.split('=')[0].strip()
            if key in updates:
                lines[i] = f"{key}={updates[key]}"
                updated_keys.add(key)
    
    # Add new keys that weren't found
    for key, value in updates.items():
        if key not in updated_keys:
            lines.append(f"{key}={value}")
    
    # Write back
    with open(file_path, 'w') as f:
        f.write('\n'.join(lines))
    
    print(f"Updated {file_path}")


def main():
    """Main function to handle port configuration."""
    if len(sys.argv) < 2:
        print("Usage: python change_ports.py <preset>")
        print("\nAvailable presets:")
        print("  default    - Reset to default ports (API:8000, Frontend:3000)")
        print("  alt        - Alternative ports (API:8080, Frontend:3001)")
        print("  custom     - Interactive custom port selection")
        print("  dev        - Development ports (API:8888, Frontend:3002)")
        sys.exit(1)
    
    preset = sys.argv[1].lower()
    
    # Get project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    backend_env = project_root / '.env'
    frontend_env = project_root / 'lapis-frontend' / '.env.local'
    
    if preset == "default":
        backend_updates = {
            'APP_PORT': '8000',
            'FRONTEND_PORT': '3000',
            'POSTGRES_PORT': '5432',
            'MONGODB_PORT': '27017',
            'REDIS_PORT': '6379',
            'REDIS_URL': 'redis://localhost:6379/0',
            'CELERY_BROKER_URL': 'redis://localhost:6379/1',
            'CELERY_RESULT_BACKEND': 'redis://localhost:6379/2',
            'FLOWER_PORT': '5555',
            'PROMETHEUS_PORT': '9090',
            'CORS_ORIGINS': 'http://localhost:3000,http://localhost:8000'
        }
        frontend_updates = {
            'NEXT_PUBLIC_API_URL': 'http://localhost:8000'
        }
        
    elif preset == "alt":
        backend_updates = {
            'APP_PORT': '8080',
            'FRONTEND_PORT': '3001',
            'POSTGRES_PORT': '5433',
            'MONGODB_PORT': '27018',
            'REDIS_PORT': '6380',
            'REDIS_URL': 'redis://localhost:6380/0',
            'CELERY_BROKER_URL': 'redis://localhost:6380/1',
            'CELERY_RESULT_BACKEND': 'redis://localhost:6380/2',
            'FLOWER_PORT': '5556',
            'PROMETHEUS_PORT': '9091',
            'CORS_ORIGINS': 'http://localhost:3001,http://localhost:8080'
        }
        frontend_updates = {
            'NEXT_PUBLIC_API_URL': 'http://localhost:8080'
        }
        
    elif preset == "dev":
        backend_updates = {
            'APP_PORT': '8888',
            'FRONTEND_PORT': '3002',
            'POSTGRES_PORT': '5434',
            'MONGODB_PORT': '27019',
            'REDIS_PORT': '6381',
            'REDIS_URL': 'redis://localhost:6381/0',
            'CELERY_BROKER_URL': 'redis://localhost:6381/1',
            'CELERY_RESULT_BACKEND': 'redis://localhost:6381/2',
            'FLOWER_PORT': '5557',
            'PROMETHEUS_PORT': '9092',
            'CORS_ORIGINS': 'http://localhost:3002,http://localhost:8888'
        }
        frontend_updates = {
            'NEXT_PUBLIC_API_URL': 'http://localhost:8888'
        }
        
    elif preset == "custom":
        print("Enter custom ports (press Enter for default):")
        
        def get_port(name, default):
            while True:
                value = input(f"{name} [{default}]: ").strip() or str(default)
                try:
                    port = int(value)
                    if 1 <= port <= 65535:
                        return port
                    else:
                        print("Port must be between 1 and 65535")
                except ValueError:
                    print("Please enter a valid number")
        
        api_port = get_port("API Port", 8000)
        frontend_port = get_port("Frontend Port", 3000)
        postgres_port = get_port("PostgreSQL Port", 5432)
        mongodb_port = get_port("MongoDB Port", 27017)
        redis_port = get_port("Redis Port", 6379)
        flower_port = get_port("Flower Port", 5555)
        prometheus_port = get_port("Prometheus Port", 9090)
        
        backend_updates = {
            'APP_PORT': str(api_port),
            'FRONTEND_PORT': str(frontend_port),
            'POSTGRES_PORT': str(postgres_port),
            'MONGODB_PORT': str(mongodb_port),
            'REDIS_PORT': str(redis_port),
            'REDIS_URL': f'redis://localhost:{redis_port}/0',
            'CELERY_BROKER_URL': f'redis://localhost:{redis_port}/1',
            'CELERY_RESULT_BACKEND': f'redis://localhost:{redis_port}/2',
            'FLOWER_PORT': str(flower_port),
            'PROMETHEUS_PORT': str(prometheus_port),
            'CORS_ORIGINS': f'http://localhost:{frontend_port},http://localhost:{api_port}'
        }
        frontend_updates = {
            'NEXT_PUBLIC_API_URL': f'http://localhost:{api_port}'
        }
        
    else:
        print(f"Unknown preset: {preset}")
        sys.exit(1)
    
    # Update files
    update_env_file(backend_env, backend_updates)
    update_env_file(frontend_env, frontend_updates)
    
    print(f"\nPort configuration updated to '{preset}' preset:")
    print(f"  API: {backend_updates['APP_PORT']}")
    print(f"  Frontend: {backend_updates['FRONTEND_PORT']}")
    print(f"  PostgreSQL: {backend_updates['POSTGRES_PORT']}")
    print(f"  MongoDB: {backend_updates['MONGODB_PORT']}")
    print(f"  Redis: {backend_updates['REDIS_PORT']}")
    print(f"  Flower: {backend_updates['FLOWER_PORT']}")
    print(f"  Prometheus: {backend_updates['PROMETHEUS_PORT']}")
    
    print(f"\nTo start services with these ports:")
    print(f"  Backend: uvicorn src.main:app --host 0.0.0.0 --port {backend_updates['APP_PORT']} --reload")
    print(f"  Frontend: cd lapis-frontend && PORT={backend_updates['FRONTEND_PORT']} npm run dev")
    print(f"  Docker: docker-compose up")


if __name__ == "__main__":
    main()