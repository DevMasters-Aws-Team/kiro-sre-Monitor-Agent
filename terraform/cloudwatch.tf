resource "aws_cloudwatch_log_group" "backend" {
  name              = "/kiro/backend"
  retention_in_days = 7
}

resource "aws_cloudwatch_log_group" "agent" {
  name              = "/kiro/agent"
  retention_in_days = 7
}

resource "aws_cloudwatch_log_group" "lambda" {
  name              = "/aws/lambda/kiro-agent"
  retention_in_days = 7
}