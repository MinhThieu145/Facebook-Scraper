# innitialize a lambda 
import csv
import json
import boto3

import pandas as pd

from datetime import datetime, timedelta

def lambda_handler(event, context):

    def PrintRecurringTime(user_id, url,channel_id , hour, minute):
        # create a new datetime object
        df = pd.DataFrame(columns=['CurrentDate','UserID','ChannelID' ,'URL', 'Hour', 'Minute'])

        # get current date 
        current_date = datetime.now().date().strftime("%Y-%m-%d")

        # set the default date
        start_time = datetime(year=1900, month = 1, day= 1, hour=0, minute=0)

        # the last hour and minute of the date (24 hours)
        last_hour = 23
        last_minute = 59
        end_time = datetime(year=1900, month = 1, day= 1, hour=last_hour, minute=last_minute)

        # create a timedelta object
        timedelta_obj = timedelta(hours=hour, minutes=minute)

        # while start_time < end_time, add the timedelta_obj to start_time
        while start_time <= end_time:
            # if smaller after add, then print
            if start_time + timedelta_obj <= end_time:
                start_time += timedelta_obj

                # append to dataframe
                df.loc[len(df)] = {'CurrentDate': current_date, 'UserID': user_id,'ChannelID': channel_id ,'URL': url,'Hour': start_time.hour, 'Minute': start_time.minute}
            else:
                start_time += timedelta_obj

        # return the dataframe
        return df



    def ReadURLData():
        # connect to s3 database
        client = boto3.client('s3')

        # url_data_path
        url_data_path = '/tmp/url_data.csv'

        client.download_file(Bucket='facebook-crawler-data',Key='url_data.csv', Filename=url_data_path)

        # read the file and loop through every line
        with open(url_data_path, 'r') as file:
            # dataframe to contain populated schedule
            populated_schedule_df = pd.DataFrame(columns=['CurrentDate', 'UserID', 'ChannelID', 'URL', 'Hour', 'Minute'])            

            reader = csv.reader(file)

            # skip the first line
            next(reader)

            # loop through every line
            for line in reader:
                user_id = line[0]
                channel_id = line[1]
                url = line[2]
                hour = int(line[3])
                minute = int(line[4])

                # print the result
                df = PrintRecurringTime(user_id=user_id,channel_id=channel_id, url=url,hour=hour,minute=minute)

                # append to populated_schedule_df
                populated_schedule_df = pd.concat([populated_schedule_df, df], ignore_index=True)

            # create a new csv file and upload to s3
            populated_schedule_df.to_csv('/tmp/populated_schedule.csv', index=False)

            # upload to s3
            client.upload_file(Bucket='facebook-crawler-data', Key='populated_schedule.csv', Filename='/tmp/populated_schedule.csv')
    


    ReadURLData()
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }