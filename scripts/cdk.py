from aws_cdk import (
    Duration,
    RemovalPolicy,
    Stack,
    Tags,
    aws_apigatewayv2,
    aws_dynamodb,
    aws_ecr,
    aws_iam,
    aws_lambda,
)
from constructs import Construct


class NationguessrStack(Stack):
    def __init__(self, scope: Construct, id_: str, **kwargs) -> None:
        super().__init__(scope, id_, **kwargs)

        # DynamoDB Table
        dynamodb_table = aws_dynamodb.Table(
            self,
            "DynamoDBTable",
            table_name="nationguessr-fsm",
            partition_key=aws_dynamodb.Attribute(
                name="chat_id", type=aws_dynamodb.AttributeType.STRING
            ),
            sort_key=aws_dynamodb.Attribute(
                name="user_id", type=aws_dynamodb.AttributeType.STRING
            ),
            billing_mode=aws_dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY,
        )
        Tags.of(dynamodb_table).add("Project", "Nationguessr")

        # API Gateway
        api_gateway = aws_apigatewayv2.HttpApi(
            self,
            "ApiGatewayV2Api",
            api_name="nationguessr-webhook",
        )
        Tags.of(api_gateway).add("Project", "Nationguessr")

        # IAM Role for Lambda
        lambda_role = aws_iam.Role(
            self,
            "IAMRole",
            assumed_by=aws_iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                aws_iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AWSLambdaBasicExecutionRole"
                )
            ],
        )
        Tags.of(lambda_role).add("Project", "Nationguessr")

        # ECR Repository
        ecr_repository = aws_ecr.Repository(
            self,
            "ECRRepository",
            repository_name="nationguessr",
            removal_policy=RemovalPolicy.DESTROY,
        )
        Tags.of(ecr_repository).add("Project", "Nationguessr")

        # Lambda Function
        lambda_function = aws_lambda.DockerImageFunction(
            self,
            "LambdaFunction",
            code=aws_lambda.DockerImageCode.from_ecr(ecr_repository),
            memory_size=1024,
            timeout=Duration.seconds(30),
            reserved_concurrent_executions=10,
            role=lambda_role,
        )
        Tags.of(lambda_function).add("Project", "Nationguessr")

        # Lambda Permission
        aws_lambda.CfnPermission(
            self,
            "LambdaPermission",
            action="lambda:InvokeFunction",
            function_name=lambda_function.function_arn,
            principal="apigateway.amazonaws.com",
            source_arn=f"arn:aws:execute-api:{self.region}:{self.account}:{api_gateway.http_api_id}/*/*/nationguessr",
        )
