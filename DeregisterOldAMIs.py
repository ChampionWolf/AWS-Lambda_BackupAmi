# Name          : AmiRetention
# Author        : TheWolf
# Functionality : 此脚本会删除超过保留期限的AMI及其关联的快照
# File version  : 1.0

# 导入模块
import boto3
import datetime

# 获取当前时间（UTC)
now = datetime.datetime.now()

# 删除旧AMI的功能实现
def deregisterOldAmis():
    print(now)
    ec2 = boto3.client('ec2')
    Amis = ec2.describe_images(Filters=[{'Name': 'description', 'Values': ['Created by AWS Lambda AMI Backup*']}])
    for ami in Amis['Images']:
        # print ami

        # 如果标记中没有指定值，则初始化AMI保留周期为默认值
        # 获取AMI保留值
        # 如果标记中指定了值，则初始化AMI保留值为此值

        amiRetention = 14  # Lambda备份脚本创建的AMI默认保留周期
        for tag in ami['Tags']:
            if tag['Key'] == 'AmiRetentionDays':
                if not tag['Value'].isdigit():
                    print("无效的 [AmiRetentionDays] 值:", tag['Value'], "请检查实例的标签设置.")
                    amiRetentionOverride = False
                    break
                amiRetentionOverride = tag['Value']
                break
            else:
                amiRetentionOverride = False
            if amiRetentionOverride:
                amiRetention = int(amiRetentionOverride)

        amiCreationDate = datetime.datetime.strptime(ami['CreationDate'], "%Y-%m-%dT%H:%M:%S.%fZ")
        amiAge = now - amiCreationDate
        if amiAge > datetime.timedelta(days=amiRetention):

            # 获取此AMI关联的快照信息
            ImageDetails = ec2.describe_images(DryRun=False, ImageIds=[ami['ImageId']])
            DeviceMappings = ImageDetails['Images'][0]['BlockDeviceMappings']
            SnapshotIds = []
            for device in DeviceMappings:
                if "Ebs" not in device:  # Skip if the device is not an EBS volume
                    continue
                SnapshotIds.append(device['Ebs']['SnapshotId'])

            # Deregister AMI
            print("AMI %s is %s hour old. Retention is set as %s days. Deleting %s." % (
            ami['ImageId'], amiAge, amiRetention, ami['ImageId']))
            ec2.deregister_image(DryRun=False, ImageId=ami['ImageId'])

            # Delete snapshots of this AMI
            for SnapshotId in SnapshotIds:
                print("Deleting ", SnapshotId)
                ec2.delete_snapshot(DryRun=False, SnapshotId=SnapshotId)

        else:
            print("AMI %s is %s hour old. Retention is set as %s days. Doing nothing." % (
            ami['ImageId'], amiAge, amiRetention,))
    return


# Main function
def deregister_ami(event, context):
    deregisterOldAmis()