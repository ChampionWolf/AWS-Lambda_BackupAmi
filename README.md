# AutoBackup AMI with Lambda
该项目是使用AWS Lambda按计划备份AMI的解决方案。通过CloudWatch Events配置执行时间。

# 使用Lambda自动化AWS备份

AWS没有提供自动备份AMI的任何解决方案。所以，通常我们都是编写Shell脚本，然后运行到一台服务器上，通过 Linux crontab 来按计划备份/删除AMI。
Lambda 提供了无需开启服务器即可运行程序/脚本的能力，再通过CloudWatch Events按计划执行，这样不仅节省了成本，也简化了配置的复杂度。

### 以下是需要在Lambda中创建的功能名称(可按需求更改)
#### AutoBackupAMI

### 您可以为EC2实例使用以下标记：

* Name                          - Any AWS supported name 
* CreateAmiBackup               - ['y', 'yes', 't', 'true', '1']
* AmiRetentionDays (optional)   - Any integer. Default 7
* AmiEternalRetentionDays (optional)    - [7,30,365]. Comma split, Set multiple times, AMI never deletes
* ExcludeDevices (optional)     - /dev/sd[b-z]. Default None
* TransferAmi (optional)        - Future option

> Tips：
> * 只要在实例添加了：CreateAmiBackup: yes ，即默认开启每日备份AMI，最多保留七天的计划
> * 结合使用 CreateAmiBackup，AmiRetentionDays， 可自定义AMI的保留周期
> * 如果需要永久保留第7天创建的AMI，则可以配置 AmiEternalRetentionDays: 7
> * 如果需要永久保留第7天及第30天创建的AMI，则可以配置 AmiEternalRetentionDays: 7,30 （注意以逗号分隔，保留周期没有限制）
> * 如果实例有多个卷，而您只想创建根卷的AMI，可以配置 ExcludeDevices: /dev/sd[b-z] 排除其他卷

### 要创建的IAM角色说明
##### 为AMI备份和AMIRetention功能提供此角色
```
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "logs:CreateLogGroup",
                "logs:CreateLogStream",
                "logs:PutLogEvents"
            ],
            "Resource": "arn:aws:logs:*:*:*"
        },
        {
            "Sid": "AmiPermissions",
            "Effect": "Allow",
            "Action": [
                "ec2:CreateImage",
                "ec2:DescribeInstances",
                "ec2:CreateTags",
                "ec2:DeregisterImage",
                "ec2:DeleteSnapshot",
                "ec2:DescribeImages"
            ],
            "Resource": [
                "*"
            ]
        }
    ]
}
```

#### Example:

* 每天备份，7天删除
* 第7天的备份保留
* 第30天的备份保留
* 第360天的备份保留

![Example](https://github.com/ChampionWolf/AWS-Lambda_BackupAmi/blob/master/Example.png?raw=true)
