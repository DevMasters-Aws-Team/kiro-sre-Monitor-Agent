# Amazon SNS - Incident Notifications
# Free tier: 1M publishes, 1K email notifications free

resource "aws_sns_topic" "incidents" {
  name = "${local.prefix}-incidents"
}

resource "aws_sns_topic" "agent_actions" {
  name = "${local.prefix}-agent-actions"
}

resource "aws_sns_topic_policy" "incidents" {
  arn = aws_sns_topic.incidents.arn

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "AllowCloudWatchAlarms"
        Effect    = "Allow"
        Principal = { Service = "cloudwatch.amazonaws.com" }
        Action    = "sns:Publish"
        Resource  = aws_sns_topic.incidents.arn
      },
      {
        Sid       = "AllowEventBridge"
        Effect    = "Allow"
        Principal = { Service = "events.amazonaws.com" }
        Action    = "sns:Publish"
        Resource  = aws_sns_topic.incidents.arn
      }
    ]
  })
}

resource "aws_sns_topic_policy" "agent_actions" {
  arn = aws_sns_topic.agent_actions.arn

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "AllowCloudWatchAlarms"
        Effect    = "Allow"
        Principal = { Service = "cloudwatch.amazonaws.com" }
        Action    = "sns:Publish"
        Resource  = aws_sns_topic.agent_actions.arn
      },
      {
        Sid       = "AllowEventBridge"
        Effect    = "Allow"
        Principal = { Service = "events.amazonaws.com" }
        Action    = "sns:Publish"
        Resource  = aws_sns_topic.agent_actions.arn
      }
    ]
  })
}

# Email subscription (only created if alert_email is provided)
resource "aws_sns_topic_subscription" "incidents_email" {
  count = var.alert_email != "" ? 1 : 0

  topic_arn = aws_sns_topic.incidents.arn
  protocol  = "email"
  endpoint  = var.alert_email
}
