# Amazon Cognito - Authentication for Dashboard
# Free tier: 50,000 MAU free with Cognito User Pool

resource "aws_cognito_user_pool" "dashboard" {
  name = "${local.prefix}-dashboard-users"

  username_attributes      = ["email"]
  auto_verified_attributes = ["email"]

  password_policy {
    minimum_length                   = 8
    require_uppercase                = true
    require_lowercase                = true
    require_numbers                  = true
    require_symbols                  = false
    temporary_password_validity_days = 7
  }

  schema {
    name                = "email"
    attribute_data_type = "String"
    required            = true
    mutable             = true

    string_attribute_constraints {
      min_length = 1
      max_length = 256
    }
  }

  account_recovery_setting {
    recovery_mechanism {
      name     = "verified_email"
      priority = 1
    }
  }
}

resource "aws_cognito_user_pool_client" "dashboard_web" {
  name         = "${local.prefix}-dashboard-web"
  user_pool_id = aws_cognito_user_pool.dashboard.id

  generate_secret = false

  explicit_auth_flows = [
    "ALLOW_USER_SRP_AUTH",
    "ALLOW_REFRESH_TOKEN_AUTH"
  ]

  supported_identity_providers = ["COGNITO"]

  prevent_user_existence_errors = "ENABLED"
}

resource "aws_cognito_user_pool_domain" "dashboard" {
  domain       = local.prefix
  user_pool_id = aws_cognito_user_pool.dashboard.id
}
