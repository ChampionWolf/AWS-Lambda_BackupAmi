# Name          : AmiRetention
# Author        : TheWolf
# Functionality : 此脚本会删除超过保留期限的AMI及其关联的快照
# File version  : 1.0

# 导入模块
import boto3
import datetime

# 获取当前时间
now = datetime.datetime.utcnow() + datetime.timedelta(hours=8)

# 删除旧AMI的功能实现
def deregisterOldAmis():
    print(now)
    ec2 = boto3.client('ec2')
    Amis = ec2.describe_images(Filters=[{'Name': 'description', 'Values': ['Created by AWS Lambda AMI Backup*']}])
    for ami in Amis['Images']:

        # 如果标记中没有指定值，则初始化AMI保留周期为默认值
        # 获取AMI保留值
        # 如果标记中指定了值，则初始化AMI保留值为此值

        amiRetention = 14
        for tag in ami['Tags']:
            if tag['Key'] == 'AmiRetentionDays':
                if not tag['Value'].isdigit():
                    print("AMI {} 拥有无效的 [AmiRetentionDays] 值:[{}],请检查AMI的标签设置.".format(ami['ImageId'],tag['Value']))
                    amiRetentionOverride = False
                    break
                amiRetentionOverride = tag['Value']
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
            try:
                for device in DeviceMappings:
                    if "Ebs" not in device:  # 跳过不是EBS卷的设备
                        continue
                    SnapshotIds.append(device['Ebs']['SnapshotId'])     # 储存快照ID
            except KeyError:
                print("快照删除成功！")

            # 取消注册AMI
            print("AMI ID:{},使用时间:{}，保留周期:{}".format(
            ami['ImageId'], amiAge, amiRetention))
            ec2.deregister_image(DryRun=False, ImageId=ami['ImageId'])

            # 删除此AMI关联的快照
            for SnapshotId in SnapshotIds:
                if ec2.delete_snapshot(DryRun=False, SnapshotId=SnapshotId):
                    print("删除成功! AMI ID:{},快照 ID:{}".format(ami['ImageId'],SnapshotId))


        else:
            print("AMI %s 已经创建了 %s 小时，计划保留时间为 %s 天，所以不会有任何操作." % (
            ami['ImageId'], amiAge, amiRetention))
    return

deregisterOldAmis()

# Main function
# def deregister_ami(event, context):
#     deregisterOldAmis()