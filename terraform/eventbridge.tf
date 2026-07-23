resource "aws_cloudwatch_event_bus" "kiro" {
  name = "${local.prefix}-events"
}

resource "aws_cloudwatch_event_rule" "agent_trigger" {
  name           = "${local.prefix}-agent-trigger"
  description    = "Captura eventos del sistema Kiro"
  event_bus_name = aws_cloudwatch_event_bus.kiro.name

  event_pattern = jsonencode({
    source = [
      "kiro.monitor"
    ]
  })
}


resource "aws_cloudwatch_event_target" "lambda" {

  event_bus_name = aws_cloudwatch_event_bus.kiro.name

  rule = aws_cloudwatch_event_rule.agent_trigger.name

  target_id = "KiroAgent"

  arn = aws_lambda_function.kiro_agent.arn
}

resource "aws_lambda_permission" "allow_eventbridge" {

  statement_id = "AllowExecutionFromEventBridge"

  action = "lambda:InvokeFunction"

  function_name = aws_lambda_function.kiro_agent.function_name

  principal = "events.amazonaws.com"

  source_arn = aws_cloudwatch_event_rule.agent_trigger.arn
}