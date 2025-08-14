# AWS EC2 Deployment Guide for Automotive Chatbot

This guide provides step-by-step instructions for deploying the Automotive Chatbot application to AWS EC2 using Terraform.

## 🚀 Quick Start

For a complete automated deployment, use the PowerShell script:

```powershell
.\scripts\quick-deploy.ps1 -Environment prod -Region us-east-1 -Domain yourdomain.com -CertificateArn "arn:aws:acm:us-east-1:123456789012:certificate/12345678-1234-1234-1234-123456789012" -MongoDbUri "mongodb+srv://user:pass@cluster.mongodb.net/dbname"
```

## 📋 Prerequisites

### Required Tools
1. **AWS CLI** - [Install AWS CLI](https://aws.amazon.com/cli/)
2. **Terraform** - [Install Terraform](https://www.terraform.io/downloads.html)
3. **PowerShell** (Windows) or **PowerShell Core** (Linux/Mac)
4. **jq** (optional but recommended) - [Install jq](https://stedolan.github.io/jq/download/)

### AWS Setup
1. **AWS Account** with appropriate permissions
2. **AWS CLI configured** with credentials:
   ```bash
   aws configure
   ```
3. **SSL Certificate** (if using custom domain) - Create in AWS Certificate Manager
4. **MongoDB Atlas** database (recommended) or MongoDB instance

## 🛠️ Deployment Options

### Option 1: Automated Deployment (Recommended)

Use the `quick-deploy.ps1` script for a complete automated deployment:

```powershell
# Navigate to the deployment directory
cd aws-deployment\scripts

# Run deployment with your parameters
.\quick-deploy.ps1 `
  -Environment prod `
  -Region us-east-1 `
  -Domain yourdomain.com `
  -CertificateArn "arn:aws:acm:us-east-1:123456789012:certificate/your-cert-id" `
  -MongoDbUri "mongodb+srv://username:password@cluster.mongodb.net/database"
```

#### Script Parameters:
- `Environment`: Deployment environment (dev, staging, prod)
- `Region`: AWS region (default: us-east-1)
- `Domain`: Your custom domain name (optional)
- `CertificateArn`: SSL certificate ARN from AWS Certificate Manager
- `MongoDbUri`: MongoDB connection string
- `DryRun`: Preview changes without applying (optional)
- `Force`: Skip confirmation prompts (optional)

### Option 2: Manual Step-by-Step Deployment

#### Step 1: Configure Environment Variables

1. Copy the example configuration:
   ```powershell
   cp terraform\terraform.tfvars.example terraform\terraform.tfvars
   ```

2. Edit `terraform.tfvars` with your values:
   ```hcl
   # Basic Configuration
   aws_region = "us-east-1"
   project_name = "automotive-chatbot"
   environment = "prod"
   
   # Domain Configuration (optional)
   domain_name = "yourdomain.com"
   certificate_arn = "arn:aws:acm:us-east-1:123456789012:certificate/your-cert-id"
   
   # Database Configuration
   mongodb_uri = "mongodb+srv://username:password@cluster.mongodb.net/database"
   jwt_secret = "your-super-secret-jwt-key"
   
   # Instance Configuration
   instance_type = "t3.medium"
   min_size = 1
   max_size = 3
   desired_capacity = 2
   ```

#### Step 2: Deploy Infrastructure

1. Navigate to terraform directory:
   ```powershell
   cd terraform
   ```

2. Initialize Terraform:
   ```powershell
   terraform init
   ```

3. Plan deployment:
   ```powershell
   terraform plan
   ```

4. Apply deployment:
   ```powershell
   terraform apply
   ```

#### Step 3: Validate Deployment

Run the validation script to ensure everything is working:

```powershell
cd ..\scripts
.\validate-deployment.ps1 -Environment prod -Region us-east-1
```

## 🌐 Domain Configuration

### Easy Domain Setup

Use the domain configuration script to easily manage domain settings:

```powershell
# Configure domain
.\scripts\configure-domain.ps1 -Domain yourdomain.com -CertificateArn "arn:aws:acm:..."

# Remove domain configuration
.\scripts\configure-domain.ps1 -RemoveDomain

# Update existing domain
.\scripts\configure-domain.ps1 -Domain newdomain.com -CertificateArn "arn:aws:acm:..." -UpdateExisting
```

### Manual Domain Setup

1. **Create SSL Certificate** in AWS Certificate Manager:
   - Go to AWS Certificate Manager in your deployment region
   - Request a public certificate for your domain
   - Validate domain ownership (DNS or email)
   - Note the certificate ARN

2. **Configure DNS**:
   - After deployment, get the ALB DNS name from Terraform outputs
   - Create a CNAME record pointing your domain to the ALB DNS name
   - Or use Route53 for automatic DNS management (included in deployment)

## 📊 Monitoring and Validation

### Health Checks

The deployment includes several health check endpoints:

- **Frontend**: `https://yourdomain.com/`
- **Backend Health**: `https://yourdomain.com/health`
- **API Health**: `https://yourdomain.com/api/health`
- **API Documentation**: `https://yourdomain.com/api/docs`

### Validation Script

Run comprehensive validation:

```powershell
# Full validation
.\scripts\validate-deployment.ps1 -Environment prod -Verbose

# Skip health checks (for faster validation)
.\scripts\validate-deployment.ps1 -Environment prod -SkipHealthChecks

# Validate with custom domain
.\scripts\validate-deployment.ps1 -Environment prod -Domain yourdomain.com
```

### CloudWatch Monitoring

The deployment automatically sets up CloudWatch monitoring:

- **Application Logs**: `/aws/ec2/automotive-chatbot/app`
- **Nginx Logs**: `/aws/ec2/automotive-chatbot/nginx`
- **Backend Logs**: `/aws/ec2/automotive-chatbot/backend`
- **Rasa Logs**: `/aws/ec2/automotive-chatbot/rasa`

## 🔧 Configuration Options

### Environment-Specific Configurations

Use pre-configured environment files:

```powershell
# Development
terraform apply -var-file="environments/dev.tfvars"

# Staging
terraform apply -var-file="environments/staging.tfvars"

# Production
terraform apply -var-file="environments/prod.tfvars"
```

### Key Configuration Parameters

| Parameter | Description | Default | Required |
|-----------|-------------|---------|----------|
| `aws_region` | AWS deployment region | us-east-1 | Yes |
| `environment` | Environment name | prod | Yes |
| `domain_name` | Custom domain | - | No |
| `certificate_arn` | SSL certificate ARN | - | If domain used |
| `mongodb_uri` | MongoDB connection string | - | Yes |
| `instance_type` | EC2 instance type | t3.medium | No |
| `min_size` | Min instances in ASG | 1 | No |
| `max_size` | Max instances in ASG | 3 | No |
| `desired_capacity` | Desired instances | 2 | No |

## 🚨 Troubleshooting

### Common Issues

1. **Certificate ARN Invalid**:
   - Ensure certificate is in the same region as deployment
   - Verify certificate is validated and issued

2. **MongoDB Connection Failed**:
   - Check MongoDB URI format
   - Ensure MongoDB Atlas allows connections from AWS
   - Verify credentials are correct

3. **Domain Not Resolving**:
   - Check DNS propagation (can take up to 48 hours)
   - Verify CNAME record points to ALB DNS name
   - Ensure certificate covers the domain

4. **Health Checks Failing**:
   - Check CloudWatch logs for application errors
   - Verify security groups allow traffic
   - Ensure instances are healthy in Auto Scaling Group

### Getting Help

1. **Check Logs**:
   ```powershell
   # View recent logs
   aws logs tail /aws/ec2/automotive-chatbot/app --follow
   ```

2. **Validate Configuration**:
   ```powershell
   terraform validate
   terraform plan
   ```

3. **Run Validation Script**:
   ```powershell
   .\scripts\validate-deployment.ps1 -Verbose
   ```

## 🔄 Updates and Maintenance

### Updating the Application

1. **Update Docker Image**:
   - Build and push new image to ECR
   - Update `docker_image_tag` in terraform.tfvars
   - Run `terraform apply`

2. **Update Configuration**:
   - Modify terraform.tfvars
   - Run `terraform plan` to preview changes
   - Run `terraform apply` to apply changes

### Scaling

```hcl
# In terraform.tfvars
min_size = 2
max_size = 5
desired_capacity = 3
```

### Backup and Recovery

- **Database**: Ensure MongoDB Atlas backups are enabled
- **Infrastructure**: Terraform state is stored in S3 with versioning
- **Application**: Docker images are versioned in ECR

## 💰 Cost Optimization

### Development Environment

```hcl
# Use smaller instances for development
instance_type = "t3.micro"
min_size = 1
max_size = 1
desired_capacity = 1
enable_nat_gateway = false  # Use NAT instance instead
```

### Production Environment

```hcl
# Optimized for production
instance_type = "t3.medium"
min_size = 2
max_size = 5
desired_capacity = 2
enable_nat_gateway = true
```

## 📞 Support

For deployment issues:

1. Check this README for common solutions
2. Run the validation script with verbose output
3. Check CloudWatch logs for application errors
4. Review Terraform plan output for configuration issues

---

**Note**: Always test deployments in a development environment before deploying to production.