variable "env_name" {
  description = "Enviroment name"
}

variable "vpc_id" {
  description = "VPC ID to attach security groups to"
}

variable "your_ip" {
  description = "Your IP for SSH access"
  default = "0.0.0.0/0"
}

