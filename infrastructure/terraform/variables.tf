variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-2"
}

variable "project_name" {
  description = "Project name"
  type        = string
  default     = "nuvii"
}

variable "environment" {
  description = "Environment (development, staging, production)"
  type        = string
  default     = "production"
}

# ECR
variable "ecr_repository_name" {
  description = "ECR repository name"
  type        = string
  default     = "nuvii-backend"
}

# ECS
variable "ecs_cluster_name" {
  description = "ECS cluster name"
  type        = string
  default     = "nuvii-cluster"
}

variable "ecs_service_name" {
  description = "ECS service name"
  type        = string
  default     = "nuvii-backend-service"
}

variable "ecs_task_definition_name" {
  description = "ECS task definition name"
  type        = string
  default     = "nuvii-backend-task"
}

variable "container_name" {
  description = "Container name"
  type        = string
  default     = "nuvii-backend"
}

variable "ecs_task_cpu" {
  description = "ECS task CPU units"
  type        = string
  default     = "512"
}

variable "ecs_task_memory" {
  description = "ECS task memory in MB"
  type        = string
  default     = "1024"
}

variable "ecs_service_desired_count" {
  description = "Desired number of ECS tasks"
  type        = number
  default     = 2
}

# RDS
variable "db_name" {
  description = "Database name"
  type        = string
  default     = "nuvii_db"
}

variable "db_username" {
  description = "Database username"
  type        = string
  default     = "nuvii_admin"
}

variable "db_password" {
  description = "Database password"
  type        = string
  sensitive   = true
}

variable "db_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t3.micro"
}

# Redis
variable "redis_node_type" {
  description = "ElastiCache Redis node type"
  type        = string
  default     = "cache.t3.micro"
}

# Secrets
variable "secret_key" {
  description = "Application secret key"
  type        = string
  sensitive   = true
}

variable "stripe_secret_key" {
  description = "Stripe secret key"
  type        = string
  sensitive   = true
}

# SSL
variable "ssl_certificate_arn" {
  description = "ARN of SSL certificate in ACM"
  type        = string
}
