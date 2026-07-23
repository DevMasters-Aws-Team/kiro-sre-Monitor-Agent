resource "aws_dynamodb_table" "knowledge" {
  name         = "${local.prefix}-KnowledgeTable"
  billing_mode = "PAY_PER_REQUEST"

  hash_key  = "errorType"
  range_key = "service"

  attribute {
    name = "errorType"
    type = "S"
  }

  attribute {
    name = "service"
    type = "S"
  }

  point_in_time_recovery {
    enabled = false
  }

  deletion_protection_enabled = false
}

resource "aws_dynamodb_table" "tickets" {
  name         = "${local.prefix}-TicketsTable"
  billing_mode = "PAY_PER_REQUEST"

  hash_key = "ticketId"

  attribute {
    name = "ticketId"
    type = "S"
  }

  point_in_time_recovery {
    enabled = false
  }

  deletion_protection_enabled = false
}

resource "aws_dynamodb_table" "incidents" {
  name         = "${local.prefix}-IncidentsTable"
  billing_mode = "PAY_PER_REQUEST"

  hash_key = "incidentId"

  attribute {
    name = "incidentId"
    type = "S"
  }

  point_in_time_recovery {
    enabled = false
  }

  deletion_protection_enabled = false
}