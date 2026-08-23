checks = [
    {
        'name': 'RootAccessKeysCheck',
        'handler': 'checks.root_access_keys_check.handler',
        'desc': 'CIS-1.1 - Root account has no active access keys',
        'policy': ['iam:GetAccountSummary']
    },
    {
        'name': 'IamMfaCheck',
        'handler': 'checks.iam_mfa_check.handler',
        'desc': 'CIS-1.3 - IAM users with console access have MFA enabled',
        'policy': ['iam:ListUsers', 'iam:GetLoginProfile', 'iam:ListMFADevices']
    },
    {
        'name': 'IamKeyRotationCheck',
        'handler': 'checks.iam_key_rotation_check.handler',
        'desc': 'CIS-1.4 - IAM access keys rotated within 90 days',
        'policy': ['iam:ListUsers', 'iam:ListAccessKeys']
    },
    {
        'name': 'IamAdminPolicyCheck',
        'handler': 'checks.iam_admin_policy_check.handler',
        'desc': 'CIS-1.5 - No IAM policies with full admin access attached directly',
        'policy': ['iam:GetAccountAuthorizationDetails']
    },
    {
        'name': 'S3PublicAccessCheck',
        'handler': 'checks.s3_public_access_check.handler',
        'desc': 'CIS-2.1 - S3 buckets are not publicly readable/writable',
        'policy': ['s3:ListAllMyBuckets', 's3:GetBucketPublicAccessBlock']
    },
    {
        'name': 'S3EncryptionCheck',
        'handler': 'checks.s3_encryption_check.handler',
        'desc': 'CIS-2.2 - S3 buckets have encryption at rest enabled',
        'policy': ['s3:ListAllMyBuckets', 's3:GetEncryptionConfiguration']
    },
    {
        'name': 'CloudTrailEnabledCheck',
        'handler': 'checks.cloudtrail_enabled_check.handler',
        'desc': 'CIS-2.3 - CloudTrail is enabled in all regions',
        'policy': ['cloudtrail:DescribeTrails', 'cloudtrail:GetTrailStatus']
    },
    {
        'name': 'CloudTrailEncryptionCheck',
        'handler': 'checks.cloudtrail_encryption_check.handler',
        'desc': 'CIS-2.4 - CloudTrail logs are encrypted',
        'policy': ['cloudtrail:DescribeTrails']
    },
    {
        'name': 'SgUnrestrictedIngressCheck',
        'handler': 'checks.sg_unrestricted_ingress_check.handler',
        'desc': 'CIS-3.1 - Security groups dont allow unrestricted ingress on 22/3389',
        'policy': ['ec2:DescribeSecurityGroups']
    },
    {
        'name': 'SgDefaultTrafficCheck',
        'handler': 'checks.sg_default_traffic_check.handler',
        'desc': 'CIS-3.2 - Default security group restricts all traffic',
        'policy': ['ec2:DescribeSecurityGroups']
    },
    {
        'name': 'EbsEncryptionCheck',
        'handler': 'checks.ebs_encryption_check.handler',
        'desc': 'CIS-4.1 - EBS volumes are encrypted',
        'policy': ['ec2:DescribeVolumes']
    }
]

with open('template.yaml', 'r') as f:
    content = f.read()

# find where Outputs: is
idx_outputs = content.find('\nOutputs:')
resources = ''
outputs = ''

for c in checks:
    func_name = c['name'] + 'Function'
    resources += f'''
  {func_name}:
    Type: AWS::Serverless::Function
    Properties:
      Handler: {c['handler']}
      CodeUri: src/
      Description: "{c['desc']}"
      Policies:
        - DynamoDBCrudPolicy:
            TableName: !Ref FindingsTable
        - Statement:
            - Effect: Allow
              Action:
'''
    for p in c['policy']:
        resources += f'                - {p}\n'
    resources += f'''              Resource: "*"
      Events:
        ScheduledCheck:
          Type: Schedule
          Properties:
            Schedule: rate(6 hours)
            Name: {c['name']}Schedule
            Description: "Runs {c['desc']}"
            Enabled: true
'''
    outputs += f'''
  {func_name}Arn:
    Description: ARN of the {c['name']} Lambda
    Value: !GetAtt {func_name}.Arn
'''

new_content = content[:idx_outputs] + resources + '\nOutputs:' + content[idx_outputs + 9:] + outputs

with open('template.yaml', 'w') as f:
    f.write(new_content)
print('Done!')
