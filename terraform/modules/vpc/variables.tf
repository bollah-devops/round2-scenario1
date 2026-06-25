variable "vpc_cidr" {
  description = "CIDR block for the vpc"
}

variable "public_subnet_cidr" {
  description = "CIDR for the public subnet"
}

variable "private_subnet_cidr" {
  description = "CIDR for the private subnet"
}

variable "env_name" {
  description = "Environment name e.g. staging"
}

variable "project_name" {
  description = "Project name"
  type        = string
}

variable "az" {
  description = "Availability zone"
  type        = string
}
