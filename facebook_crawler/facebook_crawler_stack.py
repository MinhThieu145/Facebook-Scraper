from aws_cdk import (
    Stack,
    Duration,
    aws_lambda as lmbda,
    aws_iam as iam,
    aws_apigateway as apigw,
    aws_s3 as s3,
    aws_sqs as sqs,
    aws_events as events,
    aws_events_targets as targets,
    aws_lambda_event_sources as lambda_event_sources,
    aws_lambda,
    aws_lambda_python_alpha as lambda_python_alpha, # pip install aws-cdk.aws-lambda-python-alpha

)
from constructs import Construct

# import root of lambda_functions
from facebook_crawler.lambda_functions import lambda_functions_root


# import scripts

class FacebookCrawlerStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # The code that defines your stack goes here

        # Lambda Function

        # This role only contain basic Lambda Role
        lambda_role = iam.Role.from_role_arn(
            self, "lambda_role", 'arn:aws:iam::238101178196:role/service-role/lambda_role'
        )

        # lambda role that has access to S3 and Log
        self.lambda_role_s3_log = iam.Role(
            scope=self,
            id="lambda_role_s3_log",
            role_name='LambdaRoleS3Log',
            description='lambda role that has access to S3 and Log',
            assumed_by=iam.ServicePrincipal('lambda.amazonaws.com'),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name('service-role/AWSLambdaBasicExecutionRole'),
                iam.ManagedPolicy.from_aws_managed_policy_name('AmazonS3FullAccess'),
                iam.ManagedPolicy.from_aws_managed_policy_name('CloudWatchLogsFullAccess'),
            ],  

        )

        # lambda role that allow lambda to send message to SQS, and access to S3 and Log
        self.lambda_role_sqs_s3_log = iam.Role(
            scope=self,
            id="lambda_role_sqs_s3_log",
            role_name='LambdaRoleSQSS3Log',
            description='lambda role that allow lambda to send message to SQS, and access to S3 and Log',
            assumed_by=iam.ServicePrincipal('lambda.amazonaws.com'),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name('service-role/AWSLambdaBasicExecutionRole'),
                iam.ManagedPolicy.from_aws_managed_policy_name('AmazonS3FullAccess'),
                iam.ManagedPolicy.from_aws_managed_policy_name('CloudWatchLogsFullAccess'),
                iam.ManagedPolicy.from_aws_managed_policy_name('AmazonSQSFullAccess'),
            ],
        )


        # lambda layer contains discord python package
        self.discord_layer = lambda_python_alpha.PythonLayerVersion(
            scope=self,
            id="discord_layer",
            entry="facebook_crawler/lambda_layer/discordpy_layer",
            compatible_runtimes=[lmbda.Runtime.PYTHON_3_9],
            description="discord layer for facebook crawler",
        )



        # lambda for facebook crawker
        self.lambdaFunctionCrawl = lmbda.Function(
            scope=self,
            id="lambdaFunctionCrawl",
            function_name="lambdaFunctionCrawl",
            runtime=lmbda.Runtime.PYTHON_3_9,
            code = lmbda.Code.from_asset(f"{lambda_functions_root}/lambda_crawler"),
            handler="index.lambda_handler",
            role=lambda_role,
            timeout=Duration.seconds(900),
            layers=[self.discord_layer],
        )





        # SQS to trigger lambda
        self.sqsCrawlerTrigger = sqs.Queue(
            scope=self,
            id="sqsCrawlerTrigger",
            queue_name="sqsCrawlerTrigger",
            visibility_timeout=Duration.seconds(300),# basically, just set this number to be equal (estimate) the time it takes to run your task (Lambda runtime)
            receive_message_wait_time= Duration.seconds(10), 
        )

        # get the url of SQS
        self.sqsCrawlerTrigger_url = self.sqsCrawlerTrigger.queue_url

        # Add SQS trigger for Lambda
        self.lambdaFunctionCrawl.add_event_source(lambda_event_sources.SqsEventSource(
                                                                                        queue= self.sqsCrawlerTrigger,
                                                                                        batch_size=10,
                                                                                        max_batching_window=Duration.seconds(300), # This will wait for 300 to get enough 10 message (above) to trigger lambda
                                                                                        report_batch_item_failures=True, # only put the failed message to queue
                                                                                         
                                                                                        ))
        

        # pandas lambda layer
        self.pandas_layer = lambda_python_alpha.PythonLayerVersion(
            scope=self,
            id="pandas_layer",
            entry="facebook_crawler/lambda_layer/pandas_layer",
            compatible_runtimes=[lmbda.Runtime.PYTHON_3_9],
            description="pandas layer for facebook crawler",
        )


        
        # Lambda Function to initialize schedule each and every day
        self.lambdaFunctionInitializeSchedule = lmbda.Function(
            scope=self,
            id="lambdaFunctionInitializeSchedule",
            function_name="lambdaFunctionInitializeSchedule",
            runtime=lmbda.Runtime.PYTHON_3_9,
            code = lmbda.Code.from_asset(f'{lambda_functions_root}/lambda_innitialize_schedule'),
            handler="index.lambda_handler",
            role=self.lambda_role_s3_log,
            timeout=Duration.seconds(900),
            layers=[self.pandas_layer],
        )



        # A cloudwatch event to trigger lambdaFunctionInitializeSchedule every day at exactly 00:00
        self.cloudwatchEventInitializeSchedule = events.Rule(
            scope=self,
            id="cloudwatchEventInitializeFacebookCrawlerSchedule",
            rule_name="cloudwatchEventInitializeFacebookCrawlerSchedule",
            description='A cloudwatch event to trigger lambdaFunctionInitializeSchedule every day at exactly 00:00 to initialize schedule for facebook crawler',
            schedule=events.Schedule.cron(
                minute='0',
                hour='0',
                month='*',
                week_day='*',
                year='*',
            ),
            enabled=False,
        )

        # Add Lambda trigger for cloudwatch event
        self.cloudwatchEventInitializeSchedule.add_target(target=targets.LambdaFunction(self.lambdaFunctionInitializeSchedule))


        # A lambda function to read the populated schedule and send to SQS
        self.lambdaFunctionSendScheduleToSQS = lmbda.Function(
            scope=self,
            id="lambdaFunctionSendScheduleToSQS",
            function_name="lambdaFunctionSendScheduleToSQS",
            runtime=lmbda.Runtime.PYTHON_3_9,
            code = lmbda.Code.from_asset(f'{lambda_functions_root}/lambda_send_schedule_to_sqs'),
            handler="index.lambda_handler",
            role=self.lambda_role_sqs_s3_log,
            timeout=Duration.seconds(900),
            layers=[self.pandas_layer],
        )

        # add a trigger for lambdaFunctionSendScheduleToSQS to be trigger by eventbridge in every 15 minutes
        self.cloudwatchEventSendScheduleToSQS = events.Rule(
            scope=self,
            id="cloudwatchEventSendScheduleToSQS",
            rule_name="cloudwatchEventSendScheduleToSQS",
            description='A cloudwatch event to trigger lambdaFunctionSendScheduleToSQS every 15 minutes to send schedule to SQS',
            schedule=events.Schedule.rate(Duration.minutes(15)),
            enabled=False,
        )

        # add the SQS URL of the queue as environment variable
        self.lambdaFunctionSendScheduleToSQS.add_environment("SQS_URL", self.sqsCrawlerTrigger_url)



        