data "aws_caller_identity" "current" {}

resource "aws_iam_role" "kiro_agent_role" {
  name = "${local.prefix}-agent-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = [
            "lambda.amazonaws.com"
          ]
        }
        Action = "sts:AssumeRole"
      }
    ]
  })
}

resource "aws_iam_policy" "kiro_agent_policy" {
  name = "${local.prefix}-agent-policy"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [

      {
        Effect = "Allow"
        Action = [
          "logs:*"
        ]
        Resource = "*"
      },

      {
        Effect = "Allow"
        Action = [
          "events:*"
        ]
        Resource = "*"
      },

      {
        Effect = "Allow"
        Action = [
          "lambda:InvokeFunction"
        ]
        Resource = "*"
      },

      {
        Effect = "Allow"
        Action = [
          "dynamodb:*"
        ]
        Resource = "*"
      },

      {
        Effect = "Allow"
        Action = [
          "bedrock:InvokeModel"
        ]
        Resource = "*"
      },

      {
        Sid    = "SNSPublish"
        Effect = "Allow"
        Action = [
          "sns:Publish"
        ]
        Resource = [
          "arn:aws:sns:${var.aws_region}:${data.aws_caller_identity.current.account_id}:${local.prefix}-*"
        ]
      },

      {
        Sid    = "SSMGetParameters"
        Effect = "Allow"
        Action = [
          "ssm:GetParameter",
          "ssm:GetParameters"
        ]
        Resource = [
          "arn:aws:ssm:${var.aws_region}:${data.aws_caller_identity.current.account_id}:parameter/kiro/*"
        ]
      },

      {
        Sid    = "S3ArtifactsBucket"
        Effect = "Allow"
        Action = [
          "s3:PutObject",
          "s3:GetObject"
        ]
        Resource = [
          "${aws_s3_bucket.artifacts.arn}/*"
        ]
      },

      {
        Sid    = "CognitoAdminAccess"
        Effect = "Allow"
        Action = [
          "cognito-idp:AdminGetUser",
          "cognito-idp:AdminListGroupsForUser"
        ]
        Resource = [
          aws_cognito_user_pool.dashboard.arn
        ]
      }

    ]
  })
}

resource "aws_iam_role_policy_attachment" "attach" {
  role       = aws_iam_role.kiro_agent_role.name
  policy_arn = aws_iam_policy.kiro_agent_policy.arn
}
