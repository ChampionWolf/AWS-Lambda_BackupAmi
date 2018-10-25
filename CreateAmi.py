# Name          : CreateAmi
# Author        : TheWolf
# Functionality : This function will create AMI of the EC2 instance by reading tags
# File Version  : 1.0


# 导入模块
import boto3
import datetime

import re

# 初始化全局变量
allowdWeekDayValues = ['sun', 'mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sunday', 'monday', 'tuesday', 'wednesday',
                       'thursday', 'friday', 'saturday']

# 创建AMI的功能。
def createAmi():
    # 变量
    now = datetime.datetime.now()
    today = now.day
    currentHour = now.hour
    currentMonth = now.strftime('%B')
    currentWeek = now.strftime('%A')
    currentWeekShort = now.strftime('%a')

    print("Today's is {} {} {} and current UTC hour is {}".format(currentMonth, today, currentWeek, currentHour))
    # 定义EC2
    ec2 = boto3.client('ec2')

    Reservations = ec2.describe_instances(Filters=[
        {'Name': 'tag-key', 'Values': ['CreateAmiBackup']}])  # 获取 tag=CreateAmiBackup 实例的详细信息
    for Instances in Reservations['Reservations']:
        for Instance in Instances['Instances']:

            # 初始化每次迭代的变量
            InstanceId = Instance['InstanceId']     # 获取用于创建AMI的实例ID，并为每个实例初始化以下变量
            AmiFlag = ''
            ExcludedDevices = []    # 定义排除（不创建AMI）的实例
            TransferAmiFlag = ''
            ExcludedDevicesList = []    # 定义排除（不创建AMI）的实例列表
            SkipAmi = False     # 定义默认值
            AmiDate = 1  # 如果没有指定日期，则是默认日期
            AmiTime = 0  # 如果没有指定时间，则是默认时间

            for tag in Instance['Tags']:  # 获取需要的Tag并转换

                # 检查是否设置了tag 'CreateAmiBackup'
                # 如果不是，设置 ‘SkipAmi’标记以跳过此AMI的创建

                if tag['Key'] == 'CreateAmiBackup':
                    print("正在检查是否设置了‘CreateAmiBackup’的Tag。。。")
                    CreateAmiFlag = tag['Value'].replace(' ',
                                                         '').lower()  # 删除空格并转换为小写
                    if CreateAmiFlag not in ['y', 'yes', 't', 'true',
                                             '1']:  # 如果没有设置备份AMI的标记，则退出处理剩余标记
                        print("未启用 CreateAmiBackup，跳过此AMI的创建。")
                        SkipAmi = True
                        break


                # 检查 ‘AmiBackupDates’ 是否为今天 (UTC)
                # 如果不是，设置 ‘SkipAmi’标记以跳过此AMI的创建
                elif tag['Key'] == 'AmiBackupDates':
                    print("获取AmiBackupDates标记值中。。。")
                    AmiDateList = tag['Value'].replace(' ', '').rstrip(',').split(
                        ",")  # 删除不需要的空格和逗号并将其设为列表
                    for date in AmiDateList:  # 使用Tag的值替换AMI日期的默认值
                        # print date
                        if date.isalpha():
                            if date.lower() == 'daily':
                                AmiDate = today
                                break
                            elif date.lower() in allowdWeekDayValues:
                                if date.lower() == currentWeek.lower() or currentWeekShort.lower():
                                    AmiDate = today
                                    break
                            else:
                                print("Error: Wrong date entry:" + date + ". Please correct Tag value. Expecting value Daily/[sun-sat]/[Sunday-Saturday]/[1-31] ")
                                continue
                        elif not date.isdigit() or int(date) > 31:  # 验证创建AMI的日期
                            print("Error: Wrong date entry:" + date + ". Please correct Tag value. Expecting value [1-31]/Daily/[sun-sat]/[Sunday-Saturday]")
                            continue
                        if date == str(today):
                            AmiDate = today
                            break
                    if AmiDate != today:
                        SkipAmi = True
                        break  # 如果AMI日期不是今天，则跳过


                # 检查Tag 'BackupWindowUTC' 是不是当前时间
                # 如果不是，设置 ‘SkipAmi’标记以跳过此AMI的创建
                elif tag['Key'] == 'BackupWindowUTC':
                    print("BackupWindowUTC 标记值检查中。。。")
                    AmiTimeList = tag['Value'].replace(' ', '').rstrip(',').split(",")
                    for time in AmiTimeList:  # 使用Tag的值替换AMI日期的默认值
                        # print time
                        if not time.isdigit() or int(time) > 23:  # 验证创建AMI的时间
                            print("Error: Wrong time entry:" + time + ". Please correct Tag value. Expecting value [0-23].")
                            continue
                        if int(time) == currentHour:
                            AmiTime = currentHour
                            break
                    if AmiTime != currentHour:
                        SkipAmi = True
                        break  # 如果 AmiTime 不是当前的时间，则跳过

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
                            print("Error: Wrong device name given for exclusion. It should be in the format: /dev/sd[b-z]  . Will not exclude any devices")
                            ExcludedDevicesList = []
                            # print ExcludedDevicesList
                            break
                        # print ExcludedDevicesList

            # 如果不满足条件，AMI的日期和时间将会是默认值
            print("AMI should be taken on " + str(AmiDate))
            print("AMI should be taken at " + str(AmiTime))
            if SkipAmi:
                print("条件不匹配，以下实例未创建AMI: " + InstanceId)
                break

            print("创建AMI的实例ID: %s, 服务器名称: %s" % (InstanceId, InstanceName))
            Description = "Created by AWS Lambda AMI Backup Script from %s on %s" % (InstanceId, str(now.isoformat()))
            AmiName = InstanceName +now.strftime(" - AMI taken on %Y-%m-%d at %H.%M.%S")
            print("设置AMI名称为: " + AmiName)
            print("以下设备将被排除在外: " + str(ExcludedDevicesList))
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

            AmiTags = [tag for tag in Instance['Tags'] if
                       (tag['Key'] != 'CreateAmiBackup') and (tag['Key'] != 'TransferAmi') and (
                               tag['Key'] != 'AmiBackupDates') and (
                               tag['Key'] != 'BackupWindowUTC')]  # 从标记列表中删除不需要的标记
            ec2.create_tags(Resources=[AmiId], Tags=AmiTags)  # 标记新的AMI
    return

# Main Function
def ami_backup(event, context):
    createAmi()