# define a lambda function here
# this function will be called by AWS lambda
import discord
from discord.ext import commands
import time

BOT_TOKEN = 'Your Bot Token'
CHANNEL_ID = "Your Channel ID"

def lambda_handler(event, context):
    
    intents = discord.Intents.all()
    client = commands.Bot(command_prefix='/', intents=intents)
    
    time.sleep(10)
    
    def send_message(msg):
        
        @client.event
        async def on_ready():
            channel = client.get_channel(CHANNEL_ID)
            if channel:
                await channel.send(msg)
            else:
                print("Channel not found.")
    
            await client.close()
            
        
    send_message('Scraping is done!')

    client.run(BOT_TOKEN)




# import json
# import time

# import discord
# from discord.ext import commands

# BOT_TOKEN = 'Your Bot Token'
# CHANNEL_ID = Your Channel ID


# client = commands.Bot(command_prefix='/', intents=discord.Intents.all())
# # send msg to channel
# async def send_msg(msg):
#     channel = client.get_channel(CHANNEL_ID)

#     await channel.send(msg)


# def lambda_handler(event, context):
#     # wait for 30 seconds to simulate the time for scraping
#     time.sleep(30)

#     # return the event
#     return_message = {}
#     return_message['records'] = event['Records']
#     return_message['message'] = 'Scraping is done!'

#     # send message to discord
    
#     return {
#         'statusCode': 200,
#         'body': json.dumps(return_message)

#     }