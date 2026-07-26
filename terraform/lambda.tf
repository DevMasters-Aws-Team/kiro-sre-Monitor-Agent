data "archive_file" "lambda" {
  type        = "zip"
  source_file = "${path.module}/lambda/index.py"
  output_path = "${path.module}/kiro-agent.zip"
}

resource "aws_lambda_function" "kiro_agent" {

  function_name = "${local.prefix}-agent"

  filename         = data.archive_file.lambda.output_path
  source_code_hash = data.archive_file.lambda.output_base64sha256

  role = aws_iam_role.kiro_agent_role.arn

  handler = "index.lambda_handler"

  runtime = "python3.12"

  timeout = 30

  memory_size = 256

  environment {

    variables = {

      KNOWLEDGE_TABLE = aws_dynamodb_table.knowledge.name

      TICKETS_TABLE = aws_dynamodb_table.tickets.name

      INCIDENTS_TABLE = aws_dynamodb_table.incidents.name

      ENVIRONMENT = var.environment

      SNS_INCIDENTS_TOPIC = aws_sns_topic.incidents.arn

      SNS_ACTIONS_TOPIC = aws_sns_topic.agent_actions.arn

      BEDROCK_MODEL_ID_PARAM = "/kiro/${var.environment}/bedrock/model_id"

      COGNITO_USER_POOL_ID = aws_cognito_user_pool.dashboard.id
    }
  }

  depends_on = [
    aws_iam_role_policy_attachment.attach
  ]
}