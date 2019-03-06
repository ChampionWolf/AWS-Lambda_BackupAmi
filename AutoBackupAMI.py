# Name          : AutoBackupAmi
# Author        : TheWolf
# Functionality : This function will create AMI of the EC2 instance by reading tags
# File Version  : 1.1

# 导入模块
import boto3
import datetime
from botocore.exceptions import ClientError
import re

start_time = "2019-1-10"
ec2 = boto3.client('ec2')
# 现在时间等于utc时间+8小时
now_time = (datetime.datetime.utcnow() + datetime.timedelta(hours=8)).strftime('%Y-%m-%d')


# 计算当前时间 - 脚本开始时间
def diff_time(n_time, s_time):
    """
    :param n_time: now_time
    :param s_time: start_time or AmiCreationDate
    :return d_time: The value of n_time - s_time
    """

    n_time = datetime.datetime.strptime(n_time, '%Y-%m-%d')
    s_time = datetime.datetime.strptime(s_time, '%Y-%m-%d')
    r_time = n_time - s_time
    return r_time.days


# 创建AMI的功能实现
def createAmi():
    # 定义全局变量
    global InstanceName
    # 程序总共运行了多长时间
    run_time = diff_time(now_time, start_time)

    print("Current Beijing time is: {}".format(now_time))
    # 定义EC2
    Reservations = ec2.describe_instances(Filters=[
        {'Name': 'tag-key', 'Values': ['CreateAmiBackup']}])  # 获取 tag=CreateAmiBackup 实例的详细信息
    for Instances in Reservations['Reservations']:
        for Instance in Instances['Instances']:
            # 初始化每次迭代的变量
            InstanceId = Instance['InstanceId']  # 获取用于创建AMI的实例ID，并为每个实例初始化以下变量
            AmiFlag = ''
            ExcludedDevices = []  # 定义排除（不创建AMI）的设备
            TransferAmiFlag = ''  # 未来使用
            ExcludedDevicesList = []  # 定义排除（不创建AMI）的设备列表
            SkipAmi = False  # 定义默认值
            EternalAmi = False  # 定义AMI是否永久保留
            EternalTrigger = None
            amiRetention = 7  # 备份脚本创建的AMI默认保留天数
            for tag in Instance['Tags']:  # 获取实例的Tag信息

                # 检查是否设置了tag 'CreateAmiBackup'
                # 如果不是，设置 ‘SkipAmi’标记以跳过此AMI的创建

                if tag['Key'] == 'CreateAmiBackup':
                    print("Checking if CreateAmiBackup tag is set...")
                    CreateAmiFlag = tag['Value'].replace(' ', '').lower()  # 删除空格并转换为小写
                    if CreateAmiFlag not in ['y', 'yes', 't', 'true',
                                             '1']:  # 如果没有设置开始备份AMI的标记，则退出处理剩余标记
                        print("CreateAmiBackup tag is set as skip AMI. The instanceId is: {}".format(InstanceId))
                        SkipAmi = True
                        break
                # 定义AMI是否永久保留，如果EternalAmi = True，则会添加tag到AMI
                elif tag['Key'] == 'AmiEternalRetentionDays':
                    Edays = tag['Value'].split(",")
                    for eday in Edays:
                        # print(run_time, eday)
                        if run_time % int(eday) == 0:
                            EternalTrigger = eday
                            EternalAmi = True
                            break
                        else:
                            continue

                # 获取实例的Name标签的值，Ami名称基于此
                elif tag['Key'] == 'Name':
                    InstanceName = tag['Value']

                # 排除有'ExcludeDevices'标签的设备
                # 如果指定的设备名称中有任何错误，则不会排除任何设备
                elif tag['Key'] == 'ExcludeDevices':
                    print('ExcludeDevices 标记值检查中。。。')
                    ExcludedDevices = tag['Value'].replace(' ', '').rstrip(',').split(
                        ',')  # 删除不需要的空格和逗号并将其设为列表
                    for device in ExcludedDevices:  # 循环创建排除设备列表
                        if re.match('^/dev/sd[b-z]$', device):  # 验证设备名称
                            ExcludedDevicesList.append(
                                {'DeviceName': device, 'NoDevice': ''})  # 创建排除设备的列表
                        else:
                            print("Error: Wrong device name given for exclusion. \
                            It should be in the format: /dev/sd[b-z]  . Will not exclude any devices")
                            ExcludedDevicesList = []
                            # print(ExcludedDevicesList)
                            break

            if SkipAmi:
                print("All conditions are not met. Not creating AMI of instance: " + InstanceId)
                break

            print("Creating AMI of Instance ID: %s, Sever Name: %s" % (InstanceId, InstanceName))
            Description = "Created by AWS Lambda AMI Backup Script from %s on %s" % (InstanceId, now_time)
            AmiName = InstanceName + " - AMI taken on " + now_time
            print("Setting AMI name as " + AmiName)
            print("Following devices will be excluded: " + str(ExcludedDevicesList))
            try:
                AmiResponse = ec2.create_image(DryRun=False,
                                               InstanceId=InstanceId,
                                               Name=AmiName,
                                               Description=Description,
                                               NoReboot=True,
                                               BlockDeviceMappings=ExcludedDevicesList
                                               )
                AmiId = AmiResponse['ImageId']
                if AmiResponse['ResponseMetadata']['HTTPStatusCode'] == 200:
                    print("HTTPStatusCode=200. Successfully created AMI: " + AmiId)

            except ClientError as e:
                print(e)
                break

            # AmiTags = [tag for tag in Instance['Tags'] if
            #            (tag['Key'] != 'CreateAmiBackup')
            #            and (tag['Key'] != 'AmiEternalRetentionDays')
            #            and (tag['Key'] != 'AmiRetentionDays')]  # 从标记列表中删除不需要的标记

            AmiTags = []
            for tag in Instance['Tags']:
                if tag['Key'] != 'CreateAmiBackup' and tag['Key'] != 'AmiEternalRetentionDays':
                    AmiTags.append(tag)
            if EternalAmi:
                print("AMI {} will be permanently retained".format(AmiId))
                AmiTags.append({'Key': 'EternalAmi', 'Value': 'true'})
                AmiTags.append({'Key': 'TimeTrigger', 'Value': EternalTrigger})

            print(AmiTags)
            ec2.create_tags(Resources=[AmiId], Tags=AmiTags)  # 标记新的AMI


def deregisterOldAmis():
    Amis = ec2.describe_images(Filters=[
        {
            'Name': 'description', 'Values': ['Created by AWS Lambda AMI Backup*']
        }])
    for ami in Amis['Images']:

        # 如果标记 AmiRetentionDays 中没有指定值，则初始化AMI保留周期为默认值
        # 如果标记 AmiRetentionDays 中指定了值，则初始化AMI保留值为此值

        amiRetentionOverride = False
        amiRetention = 7  # Lambda备份脚本创建的AMI的默认保留期
        EternalAmi = False
        for tag in ami['Tags']:
            if tag['Key'] == 'EternalAmi' and tag['Value'].lower() == 'true':
                EternalAmi = True
                break
            if tag['Key'] == 'AmiRetentionDays':
                if not tag['Value'].isdigit():
                    print("Value set for tag AmiRetentionDays =", tag['Value'], "is Invalid. Using default retention")
                    amiRetentionOverride = False
                    break
                amiRetentionOverride = tag['Value']
                break
            else:
                amiRetentionOverride = False

        if EternalAmi:
            continue

        if amiRetentionOverride:
            amiRetention = int(amiRetentionOverride)

        amiCreationDate = (ami['CreationDate']).split("T")[0]
        amiAge = diff_time(now_time, amiCreationDate)

        if amiAge > datetime.timedelta(days=amiRetention).days:
            # 获取此AMI关联的快照信息

            ImageDetails = ec2.describe_images(DryRun=False, ImageIds=[ami['ImageId']])
            DeviceMappings = ImageDetails['Images'][0]['BlockDeviceMappings']
            SnapshotIds = []
            for device in DeviceMappings:
                if 'Ebs' not in device:  # 跳过不是EBS的设备
                    continue
                SnapshotIds.append(device['Ebs']['SnapshotId'])  # 储存快照ID

            # 取消注册AMI AMI
            print("AMI {0} is {1} day. Retention is set as {2} days. Deleting {0}.".format(
                ami['ImageId'], amiAge, amiRetention))
            try:
                ec2.deregister_image(DryRun=False, ImageId=ami['ImageId'])

                # 删除这个AMI的快照
                # for SnapshotId in SnapshotIds:
                #     print("Deleting ", SnapshotId)
                #     ec2.delete_snapshot(DryRun=False, SnapshotId=SnapshotId)
            except ClientError as e:
                print(e)

        else:
            print("AMI {} is {} day. Retention is set as {} days. Doing nothing.".format(
                ami['ImageId'], amiAge, amiRetention))


# createAmi()
# deregisterOldAmis()

# Main Function
def run(event, context):
    createAmi()
    deregisterOldAmis()
