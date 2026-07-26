# AWS Systems Manager Parameter Store - Configuration & Secrets
# Free tier: Standard parameters are free (up to 10,000)

resource "aws_ssm_parameter" "bedrock_model_id" {
  name  = "/kiro/${var.environment}/bedrock/model_id"
  type  = "String"
  value = "anthropic.claude-3-sonnet-20240229-v1:0"
}

resource "aws_ssm_parameter" "bedrock_region" {
  name  = "/kiro/${var.environment}/bedrock/region"
  type  = "String"
  value = var.aws_region
}

resource "aws_ssm_parameter" "bedrock_max_tokens" {
  name  = "/kiro/${var.environment}/bedrock/max_tokens"
  type  = "String"
  value = "4096"
}

resource "aws_ssm_parameter" "bedrock_temperature" {
  name  = "/kiro/${var.environment}/bedrock/temperature"
  type  = "String"
  value = "0.1"
}

resource "aws_ssm_parameter" "agent_max_retries" {
  name  = "/kiro/${var.environment}/agent/max_retries"
  type  = "String"
  value = "3"
}

resource "aws_ssm_parameter" "agent_debounce_seconds" {
  name  = "/kiro/${var.environment}/agent/debounce_seconds"
  type  = "String"
  value = "10"
}

resource "aws_ssm_parameter" "agent_confidence_threshold" {
  name  = "/kiro/${var.environment}/agent/confidence_threshold"
  type  = "String"
  value = "0.9"
}

resource "aws_ssm_parameter" "sns_topic_arn" {
  name  = "/kiro/${var.environment}/sns/topic_arn"
  type  = "String"
  value = aws_sns_topic.incidents.arn
}

resource "aws_ssm_parameter" "cognito_user_pool_id" {
  name  = "/kiro/${var.environment}/cognito/user_pool_id"
  type  = "String"
  value = aws_cognito_user_pool.dashboard.id
}

resource "aws_ssm_parameter" "cognito_client_id" {
  name  = "/kiro/${var.environment}/cognito/client_id"
  type  = "String"
  value = aws_cognito_user_pool_client.dashboard_web.id
}
