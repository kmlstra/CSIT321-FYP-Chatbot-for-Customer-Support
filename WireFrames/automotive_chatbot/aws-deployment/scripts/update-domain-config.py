#!/usr/bin/env python3
"""
Domain Configuration Update Script
This script reads the domain-config.json file and updates all configuration files
with the appropriate domain settings for the specified environment.
"""

import json
import os
import sys
import re
from pathlib import Path

def load_domain_config(config_path):
    """Load domain configuration from JSON file"""
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: Configuration file not found at {config_path}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in configuration file: {e}")
        sys.exit(1)

def update_nginx_config(config, environment, nginx_path):
    """Update nginx configuration with domain settings"""
    domains = config['domains'][environment]
    
    nginx_template = f"""
server {{
    listen 80;
    server_name {domains['main_domain']} www.{domains['main_domain']};
    
    # Redirect HTTP to HTTPS
    {'return 301 https://$server_name$request_uri;' if domains['ssl_enabled'] else ''}
    
    location / {{
        proxy_pass http://frontend:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }}
}}

# API Server
server {{
    listen 80;
    server_name {domains['api_domain']};
    
    {'return 301 https://$server_name$request_uri;' if domains['ssl_enabled'] else ''}
    
    location / {{
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }}
}}

# Widget Server
server {{
    listen 80;
    server_name {domains['widget_domain']};
    
    {'return 301 https://$server_name$request_uri;' if domains['ssl_enabled'] else ''}
    
    location / {{
        proxy_pass http://backend:8000/api/widget;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }}
}}
"""
    
    if domains['ssl_enabled']:
        nginx_template += f"""
# HTTPS Configuration
server {{
    listen 443 ssl http2;
    server_name {domains['main_domain']} www.{domains['main_domain']};
    
    ssl_certificate /etc/letsencrypt/live/{domains['main_domain']}/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/{domains['main_domain']}/privkey.pem;
    
    location / {{
        proxy_pass http://frontend:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }}
}}

server {{
    listen 443 ssl http2;
    server_name {domains['api_domain']};
    
    ssl_certificate /etc/letsencrypt/live/{domains['api_domain']}/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/{domains['api_domain']}/privkey.pem;
    
    location / {{
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }}
}}

server {{
    listen 443 ssl http2;
    server_name {domains['widget_domain']};
    
    ssl_certificate /etc/letsencrypt/live/{domains['widget_domain']}/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/{domains['widget_domain']}/privkey.pem;
    
    location / {{
        proxy_pass http://backend:8000/api/widget;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }}
}}
"""
    
    with open(nginx_path, 'w') as f:
        f.write(nginx_template)
    
    print(f"✓ Updated nginx configuration for {environment} environment")

def update_docker_compose(config, environment, compose_path):
    """Update docker-compose file with environment variables"""
    domains = config['domains'][environment]
    
    # Read existing docker-compose file
    with open(compose_path, 'r') as f:
        content = f.read()
    
    # Update environment variables
    env_vars = {
        'MAIN_DOMAIN': domains['main_domain'],
        'API_DOMAIN': domains['api_domain'],
        'WIDGET_DOMAIN': domains['widget_domain'],
        'ADMIN_DOMAIN': domains['admin_domain'],
        'SSL_ENABLED': str(domains['ssl_enabled']).lower(),
        'FORCE_HTTPS': str(domains['force_https']).lower(),
        'SSL_EMAIL': config['ssl']['email']
    }
    
    # Add environment section to backend service if not exists
    if 'environment:' not in content:
        # Find backend service and add environment section
        backend_pattern = r'(backend:.*?)(\n  [a-z]|\n[a-z]|$)'
        replacement = r'\1\n    environment:\n'
        for key, value in env_vars.items():
            replacement += f'      - {key}={value}\n'
        replacement += r'\2'
        content = re.sub(backend_pattern, replacement, content, flags=re.DOTALL)
    
    with open(compose_path, 'w') as f:
        f.write(content)
    
    print(f"✓ Updated docker-compose configuration for {environment} environment")

def update_terraform_vars(config, environment, tfvars_path):
    """Update Terraform variables file"""
    domains = config['domains'][environment]
    
    tfvars_content = f"""
# Domain Configuration
main_domain = "{domains['main_domain']}"
api_domain = "{domains['api_domain']}"
widget_domain = "{domains['widget_domain']}"
admin_domain = "{domains['admin_domain']}"

# SSL Configuration
ssl_enabled = {str(domains['ssl_enabled']).lower()}
ssl_email = "{config['ssl']['email']}"

# Environment
environment = "{environment}"

# Instance Configuration
instance_type = "t3.medium"
min_size = 1
max_size = 3
desired_capacity = 2

# Database
mongodb_atlas_uri = "{config['database']['mongodb_atlas_uri']}"
database_name = "{config['database']['database_name']}"
"""
    
    with open(tfvars_path, 'w') as f:
        f.write(tfvars_content)
    
    print(f"✓ Updated Terraform variables for {environment} environment")

def create_env_file(config, environment, env_path):
    """Create environment file for the application"""
    domains = config['domains'][environment]
    
    env_content = f"""
# Domain Configuration
MAIN_DOMAIN={domains['main_domain']}
API_DOMAIN={domains['api_domain']}
WIDGET_DOMAIN={domains['widget_domain']}
ADMIN_DOMAIN={domains['admin_domain']}

# SSL Configuration
SSL_ENABLED={str(domains['ssl_enabled']).lower()}
FORCE_HTTPS={str(domains['force_https']).lower()}
SSL_EMAIL={config['ssl']['email']}

# CORS Configuration
CORS_ORIGINS={','.join(config['cors']['allowed_origins'])}

# Database Configuration
MONGODB_ATLAS_URI={config['database']['mongodb_atlas_uri']}
DATABASE_NAME={config['database']['database_name']}

# External Services
RASA_URL={config['external_services']['rasa_url']}
ACTIONS_URL={config['external_services']['actions_url']}

# Environment
ENVIRONMENT={environment}
"""
    
    with open(env_path, 'w') as f:
        f.write(env_content)
    
    print(f"✓ Created environment file for {environment} environment")

def main():
    if len(sys.argv) != 2:
        print("Usage: python update-domain-config.py <environment>")
        print("Available environments: production, staging, development")
        sys.exit(1)
    
    environment = sys.argv[1]
    
    # Get script directory
    script_dir = Path(__file__).parent
    aws_deployment_dir = script_dir.parent
    
    # Load configuration
    config_path = aws_deployment_dir / 'config' / 'domain-config.json'
    config = load_domain_config(config_path)
    
    if environment not in config['domains']:
        print(f"Error: Environment '{environment}' not found in configuration")
        print(f"Available environments: {', '.join(config['domains'].keys())}")
        sys.exit(1)
    
    print(f"Updating configuration for {environment} environment...")
    
    # Update configuration files
    nginx_path = aws_deployment_dir / 'docker' / 'nginx.conf'
    compose_path = aws_deployment_dir / 'docker' / 'docker-compose.prod.yml'
    tfvars_path = aws_deployment_dir / 'terraform' / 'environments' / f'{environment}.tfvars'
    env_path = aws_deployment_dir / 'environments' / f'.env.{environment}'
    
    # Ensure directories exist
    env_path.parent.mkdir(exist_ok=True)
    
    # Update all configuration files
    update_nginx_config(config, environment, nginx_path)
    update_docker_compose(config, environment, compose_path)
    update_terraform_vars(config, environment, tfvars_path)
    create_env_file(config, environment, env_path)
    
    print(f"\n✅ Successfully updated all configuration files for {environment} environment!")
    print(f"\nNext steps:")
    print(f"1. Review the generated configuration files")
    print(f"2. Update your DNS records to point to your EC2 instance")
    print(f"3. Run the deployment: ./deploy.sh {environment}")

if __name__ == '__main__':
    main()