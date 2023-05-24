# define lambda function

import json
import csv
import os

import pandas as pd
import datetime

import boto3

def lambda_handler(event, context):

    # create a url_list
    url_list = []


    # the ARN of queue from environment variable
    queue_url = os.environ['SQS_URL']

    # get current time (only hour and minute)
    current_time = datetime.datetime.now().time()
    current_hour = current_time.hour
    current_minute = current_time.minute

    # get data from s3
    def GetDataFromS3():
        # connect to s3 database
        client = boto3.client('s3')

        # populated_schedule_data_path
        populated_schedule_data_path = '/tmp/populated_schedule.csv'

        # download
        client.download_file(Bucket='facebook-crawler-data',Key='populated_schedule.csv', Filename=populated_schedule_data_path)

        # read csv
        df = pd.read_csv(populated_schedule_data_path)

        return df


    matching_urls = []

    # Loop through the dataframe and check for approximate matches
    df = GetDataFromS3()
    for index, row in df.iterrows():
        hour = row['Hour']
        minute = row['Minute']

        # Check if the hour and minute fall within the approximate range
        if (
            current_hour - 3 <= hour <= current_hour + 3 and
            current_minute - 3 <= minute <= current_minute + 3
        ):
            matching_urls.append(row['URL'])

    # Print the matching URLs
    for url in matching_urls:
        print(url)

        # send message to SQS
        sqs = boto3.client('sqs')
        response = sqs.send_message(
            QueueUrl=queue_url,
            MessageBody=url
        )

        # add to url_list
        url_list.append(url)

    return {
        # status code
        'statusCode': 200,
        # a body saying Hi from lambda to SQS
        'urlList': url_list
    }