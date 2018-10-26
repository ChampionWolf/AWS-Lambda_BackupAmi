import boto3
import time
import datetime

now = datetime.datetime.utcnow() + datetime.timedelta(hours=8)

ec2 = boto3.client('ec2')
# Amis = ec2.describe_images(Filters=[{'Name': 'description', 'Values': ['Created by AWS Lambda AMI Backup*']}])



#
# for ami in Amis['Images']:
#     for tag in ami['Tags']:
#         print(tag)
#         if tag['Key'] == 'AmiRetentionDays':
#             if not tag['Value'].isdigit():
#                 print("{} 拥有无效的 [AmiRetentionDays] 值:[{}],请检查实例的标签设置.".format(ami['ImageId'],tag['Value']))
#                 amiRetentionOverride = False
#                 break
#             amiRetentionOverride = tag['Value']
#             break
#         else:
#             amiRetentionOverride = False
#         if amiRetentionOverride:
#             amiRetention = int(amiRetentionOverride)
#
#
#     amiCreationDate = datetime.datetime.strptime(ami['CreationDate'], "%Y-%m-%dT%H:%M:%S.%fZ")
#     amiAge = now - amiCreationDate
#
#     # if amiAge > datetime.timedelta(days=amiRetention):
#     #     print(amiAge)
