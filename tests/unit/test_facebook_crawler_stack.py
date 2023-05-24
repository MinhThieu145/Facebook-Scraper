import aws_cdk as core
import aws_cdk.assertions as assertions

from facebook_crawler.facebook_crawler_stack import FacebookCrawlerStack

# example tests. To run these tests, uncomment this file along with the example
# resource in facebook_crawler/facebook_crawler_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = FacebookCrawlerStack(app, "facebook-crawler")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
