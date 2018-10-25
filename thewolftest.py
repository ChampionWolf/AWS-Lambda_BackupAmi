import boto3
import time
import datetime

now = datetime.datetime.now()
today = now.day
currentHour = now.hour
currentMonth = now.strftime('%B')
currentWeek = now.strftime('%A')
currentWeekShort = now.strftime('%a')
def deregisterOldAmis():
    print(now)
    ec2 = boto3.client('ec2')
    Amis = ec2.describe_images(Filters=[{'Name': 'description', 'Values': ['Created by AWS Lambda AMI Backup*']}])
    print(Amis)
    for ami in Amis['Images']:
        ImageDetails = ec2.describe_images(DryRun=False, ImageIds=[ami['ImageId']])
        DeviceMappings = ImageDetails['Images'][0]['BlockDeviceMappings']
        print(ImageDetails)
        print(DeviceMappings)

deregisterOldAmis()
