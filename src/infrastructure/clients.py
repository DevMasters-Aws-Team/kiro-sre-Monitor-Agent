"""AWS Infrastructure Clients - Mock support for local testing."""

import logging
from typing import Any
from unittest.mock import MagicMock, AsyncMock

from src.config import settings

logger = logging.getLogger(__name__)

# Use setting from config (reads from .env or defaults to True)
USE_MOCK_AWS = settings.use_mock_aws


class MockDynamoDBClient:
    """Mock DynamoDB client for local testing."""

    def __init__(self):
        self.tables: dict[str, list[dict]] = {
            "KnowledgeTable": [],
            "TicketsTable": [],
            "IncidentsTable": [],
            "AuditTable": [],
        }

    def get_item(self, TableName: str, Key: dict) -> dict | None:
        table = self.tables.get(TableName, [])
        for item in table:
            if all(item.get(k) == v for k, v in Key.items()):
                return {"Item": item}
        return None

    def put_item(self, TableName: str, Item: dict) -> dict:
        if TableName not in self.tables:
            self.tables[TableName] = []
        self.tables[TableName].append(Item)
        logger.info("MockDynamoDB: put_item to %s", TableName)
        return {"ResponseMetadata": {"HTTPStatusCode": 200}}

    def query(self, TableName: str, KeyConditionExpression: str, **kwargs) -> dict:
        table = self.tables.get(TableName, [])
        return {"Items": table, "Count": len(table)}

    def update_item(self, TableName: str, Key: dict, UpdateExpression: str, **kwargs) -> dict:
        logger.info("MockDynamoDB: update_item in %s", TableName)
        return {"ResponseMetadata": {"HTTPStatusCode": 200}}


class MockCloudWatchLogsClient:
    """Mock CloudWatch Logs client for local testing."""

    def __init__(self):
        self.logs: list[dict] = []

    def filter_log_events(self, **kwargs) -> dict:
        log_group = kwargs.get("logGroupName", "")
        filter_pattern = kwargs.get("filterPattern", "")
        limit = kwargs.get("limit", 50)

        # Return mock error logs for testing
        mock_events = [
            {
                "timestamp": 1234567890000,
                "message": '{"level":"ERROR","service":"payment-service","endpoint":"POST /api/v1/sales/pay","status_code":503,"error_type":"DatabaseTimeoutError","message":"Connection timeout acquiring connection from pool","trace_id":"tr-test123","duration_ms":3500}',
            },
            {
                "timestamp": 1234567891000,
                "message": '{"level":"ERROR","service":"order-service","endpoint":"POST /api/v1/purchase/checkout","status_code":500,"error_type":"InternalServerError","message":"Unexpected error during checkout","trace_id":"tr-test456","duration_ms":2800}',
            },
        ]

        filtered = mock_events[:limit]
        return {"events": filtered, "nextToken": None}


class MockECSClient:
    """Mock ECS client for local testing."""

    def update_service(self, cluster: str, service: str, forceNewDeployment: bool = False, desiredCount: int = None) -> dict:
        logger.info("MockECS: update_service %s/%s (force=%s, count=%s)", cluster, service, forceNewDeployment, desiredCount)
        return {"service": {"serviceName": service, "status": "ACTIVE"}}


class MockSQSClient:
    """Mock SQS client for local testing."""

    def purge_queue(self, QueueUrl: str) -> dict:
        logger.info("MockSQS: purge_queue %s", QueueUrl)
        return {"ResponseMetadata": {"HTTPStatusCode": 200}}


class MockElastiCacheClient:
    """Mock ElastiCache/Redis client for local testing."""

    def __init__(self):
        self.cache: dict[str, Any] = {}

    def delete(self, *keys: str) -> int:
        deleted = 0
        for key in keys:
            if key in self.cache:
                del self.cache[key]
                deleted += 1
        logger.info("MockRedis: deleted %d keys", deleted)
        return deleted


class MockEventBridgeClient:
    """Mock EventBridge client for local testing."""

    def __init__(self):
        self.events: list[dict] = []

    def put_events(self, Entries: list[dict]) -> dict:
        self.events.extend(Entries)
        logger.info("MockEventBridge: put_events (%d events)", len(Entries))
        return {"FailedEntryCount": 0, "Entries": [{"EventId": f"mock-event-{i}"} for i in range(len(Entries))]}


def _get_boto3_credentials():
    """Get boto3 credentials from settings."""
    from src.config import settings
    
    kwargs = {"region_name": settings.aws_region}
    
    # Add credentials if provided (not None)
    if settings.aws_access_key_id:
        kwargs["aws_access_key_id"] = settings.aws_access_key_id
    if settings.aws_secret_access_key:
        kwargs["aws_secret_access_key"] = settings.aws_secret_access_key
    if settings.aws_session_token:
        kwargs["aws_session_token"] = settings.aws_session_token
    
    return kwargs


class AWSClients:
    """Factory for AWS clients (mock or real based on environment)."""

    def __init__(self):
        self._dynamodb = None
        self._cloudwatch_logs = None
        self._ecs = None
        self._sqs = None
        self._elasticache = None
        self._eventbridge = None

    @property
    def dynamodb(self):
        if self._dynamodb is None:
            if USE_MOCK_AWS:
                self._dynamodb = MockDynamoDBClient()
            else:
                import boto3
                self._dynamodb = boto3.client("dynamodb", **_get_boto3_credentials())
        return self._dynamodb

    @property
    def cloudwatch_logs(self):
        if self._cloudwatch_logs is None:
            if USE_MOCK_AWS:
                self._cloudwatch_logs = MockCloudWatchLogsClient()
            else:
                import boto3
                self._cloudwatch_logs = boto3.client("logs", **_get_boto3_credentials())
        return self._cloudwatch_logs

    @property
    def ecs(self):
        if self._ecs is None:
            if USE_MOCK_AWS:
                self._ecs = MockECSClient()
            else:
                import boto3
                self._ecs = boto3.client("ecs", **_get_boto3_credentials())
        return self._ecs

    @property
    def sqs(self):
        if self._sqs is None:
            if USE_MOCK_AWS:
                self._sqs = MockSQSClient()
            else:
                import boto3
                self._sqs = boto3.client("sqs", **_get_boto3_credentials())
        return self._sqs

    @property
    def elasticache(self):
        if self._elasticache is None:
            if USE_MOCK_AWS:
                self._elasticache = MockElastiCacheClient()
            else:
                import boto3
                self._elasticache = boto3.client("elasticache", **_get_boto3_credentials())
        return self._elasticache

    @property
    def eventbridge(self):
        if self._eventbridge is None:
            if USE_MOCK_AWS:
                self._eventbridge = MockEventBridgeClient()
            else:
                import boto3
                self._eventbridge = boto3.client("events", **_get_boto3_credentials())
        return self._eventbridge


# Singleton instance
aws_clients = AWSClients()
