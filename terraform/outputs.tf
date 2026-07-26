output "project" {
  value = local.prefix
}
output "knowledge_table" {
  value = aws_dynamodb_table.knowledge.name
}

output "tickets_table" {
  value = aws_dynamodb_table.tickets.name
}

output "incidents_table" {
  value = aws_dynamodb_table.incidents.name
}
output "backend_log_group" {
  value = aws_cloudwatch_log_group.backend.name
}

output "agent_log_group" {
  value = aws_cloudwatch_log_group.agent.name
}

output "lambda_log_group" {
  value = aws_cloudwatch_log_group.lambda.name
}
output "event_bus_name" {
  value = aws_cloudwatch_event_bus.kiro.name
}

output "event_rule_name" {
  value = aws_cloudwatch_event_rule.agent_trigger.name
}
output "lambda_name" {
  value = aws_lambda_function.kiro_agent.function_name
}

output "lambda_arn" {
  value = aws_lambda_function.kiro_agent.arn
}

# --- Cognito Outputs ---

output "cognito_user_pool_id" {
  value = aws_cognito_user_pool.dashboard.id
}

output "cognito_client_id" {
  value = aws_cognito_user_pool_client.dashboard_web.id
}

output "cognito_domain" {
  value = aws_cognito_user_pool_domain.dashboard.domain
}

# --- S3 Outputs ---

output "s3_frontend_bucket" {
  value = aws_s3_bucket.frontend.id
}

output "s3_frontend_website_endpoint" {
  value = aws_s3_bucket_website_configuration.frontend.website_endpoint
}

output "s3_artifacts_bucket" {
  value = aws_s3_bucket.artifacts.id
}

# --- SNS Outputs ---

output "sns_incidents_topic_arn" {
  value = aws_sns_topic.incidents.arn
}

output "sns_agent_actions_topic_arn" {
  value = aws_sns_topic.agent_actions.arn
}
