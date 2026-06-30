# Round 2 - Scenario 1: E-commerce API Platform

## What this project does
A complete e-commerce REST API deployed across two fully isolated AWS environments
(staging and production), with automated CI/CD via Jenkins and a serverless
auto-shutdown system to control infrastructure costs.

## Architecture

    Developer pushes code to GitHub
            |
            v
    Jenkins detects new commit
            |
            v
    Stage 1: Build Docker image, push to Docker Hub
            |
            v
    Stage 2: Deploy to staging  (Ansible, --limit staging)
            |
            v
    Stage 3: Deploy to production (Ansible, --limit production)
            |
            v
    Nightly: EventBridge triggers Lambda -> stops untagged EC2 instances

## Tech stack
- Terraform - infrastructure as code (VPC, EC2, security groups, CloudWatch alarms)
- Flask - REST API (products, cart, health)
- Docker - containerization
- Ansible - configuration management, deployed to both environments from one playbook
- Nginx - reverse proxy
- Jenkins - CI/CD pipeline
- AWS Lambda + EventBridge - automated cost control
- boto3 - AWS SDK used inside the Lambda function

## API Endpoints

| Method | Path         | Description                          |
|--------|--------------|---------------------------------------|
| GET    | /            | API overview and available routes     |
| GET    | /products    | Full product catalogue                |
| GET    | /cart        | Current cart contents and subtotal    |
| POST   | /cart/add    | Add an item to the cart                |
| GET    | /health      | Health check with live system status  |

## Environments

| Setting      | Staging                  | Production                 |
|--------------|---------------------------|------------------------------|
| VPC CIDR     | 10.5.0.0/16               | 10.6.0.0/16                  |
| Container    | staging-app                | production-app                |
| ENV_NAME     | staging                    | production                    |

Both environments run the identical Docker image - only configuration differs,
proving true environment parity.

## How to deploy

### 1 - Provision infrastructure

    cd terraform/environments/staging
    terraform init
    terraform apply -auto-approve

    cd ../production
    terraform init
    terraform apply -auto-approve

### 2 - Update Ansible inventory with the new IPs
Edit ansible/inventory.ini with the staging and production public IPs from
the Terraform output.

### 3 - Deploy manually (or let Jenkins do it on git push)

    ansible-playbook -i ansible/inventory.ini ansible/playbook.yml \
      -e "env_name=staging" --limit staging

    ansible-playbook -i ansible/inventory.ini ansible/playbook.yml \
      -e "env_name=production" --limit production

### 4 - Deploy the Lambda auto-shutdown system

    cd lambda
    terraform init
    terraform apply -auto-approve

## IMPORTANT - the --limit flag

Always include --limit staging or --limit production when running the
playbook. Without it, hosts: all in the playbook applies the env_name
variable to BOTH servers, overwriting whichever one ran last. This was a
real bug caught and fixed during development - see the Jenkinsfile for
the corrected pipeline stages.

## Cost protection

The Lambda function (lambda/auto_shutdown.py) runs every night at midnight UTC
via EventBridge. It stops any running EC2 instance that does NOT have the tag
KeepRunning=true. The HFM Trading Bot is tagged accordingly and is never touched.

Test it manually:

    aws lambda invoke --function-name ec2-auto-shutdown \
      --payload '{}' --cli-binary-format raw-in-base64-out response.json
    cat response.json

## Key lessons from this project
- Always use --limit when running a playbook with hosts: all against
  multiple environments in the same inventory
- t3.micro avoids vCPU bucket conflicts with existing t2.micro instances
- Terraform module outputs must use direct references (aws_vpc.main.id),
  never quoted strings
- ignore_errors is a task-level directive, not a module parameter
- boto3 dictionary keys are case-sensitive (Filters, Values, Reservations)
- Lambda + EventBridge is the only way to reliably stop forgotten resources
  when you are not at your computer
