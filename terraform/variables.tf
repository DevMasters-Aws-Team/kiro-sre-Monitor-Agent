variable "aws_region" {
  type    = string
  default = "us-east-1"
}

variable "project_name" {
  type    = string
  default = "kiro-monitor"
}

variable "environment" {
  type    = string
  default = "dev"
}

variable "alert_email" {
  description = "Email address for SNS incident alert notifications"
  type        = string
  default     = ""
}
