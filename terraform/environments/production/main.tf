module "vpc" {
  source              = "../../modules/vpc"
  env_name            = "production"
  project_name        = "scenario1-platform"
  vpc_cidr            = "10.6.0.0/16"
  public_subnet_cidr  = "10.6.1.0/24"
  private_subnet_cidr = "10.6.2.0/24"
  az                  = "us-east-1a"
}

module "security_groups" {
  source   = "../../modules/security_groups"
  env_name = "production"
  vpc_id   = module.vpc.vpc_id
  your_ip  = var.your_ip
}

module "ec2" {
  source            = "../../modules/ec2"
  env_name          = "production"
  public_subnet_id  = module.vpc.public_subnet_id
  private_subnet_id = module.vpc.private_subnet_id
  key_name          = var.key_name
  app_sg_id         = module.security_groups.app_sg_id
}

resource "aws_cloudwatch_metric_alarm" "cpu_high" {
  alarm_name          = "production-cpu-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "CPUUtilization"
  namespace           = "AWS/EC2"
  period              = 60
  statistic           = "Average"
  threshold           = 80
  alarm_description   = "CPU above 80% for 2 minutes"
  dimensions = {
    InstanceId = module.ec2.app_instance_id
  }
}
