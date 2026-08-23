import yaml
from collections import OrderedDict

# Setup for keeping YAML order and structure
def setup_yaml():
    class OrderedDumper(yaml.SafeDumper):
        pass
    def dict_representer(dumper, data):
        return dumper.represent_dict(data.items())
    OrderedDumper.add_representer(OrderedDict, dict_representer)
    OrderedDumper.add_representer(dict, dict_representer)
    
    class OrderedLoader(yaml.SafeLoader):
        pass
    def dict_constructor(loader, node):
        return OrderedDict(loader.construct_pairs(node))
    OrderedLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, dict_constructor)
    
    return OrderedLoader, OrderedDumper

Loader, Dumper = setup_yaml()

with open('template.yaml', 'r') as f:
    template = yaml.load(f, Loader=Loader)

# Note: The AWSTemplateFormatVersion and Transform are sometimes dropped or loaded wrong by PyYAML,
# but we will just write them out directly and use the OrderedDict for the rest.
# Let's clean up any Transform/AWSTemplateFormatVersion from the loaded template if they exist
template.pop('AWSTemplateFormatVersion', None)
template.pop('Transform', None)

# Add 11 functions
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

for check in checks:
    func_name = f"{check['name']}Function"
    template['Resources'][func_name] = OrderedDict([
        ('Type', 'AWS::Serverless::Function'),
        ('Properties', OrderedDict([
            ('Handler', check['handler']),
            ('CodeUri', 'src/'),
            ('Description', check['desc']),
            ('Policies', [
                {'DynamoDBCrudPolicy': {'TableName': {'Ref': 'FindingsTable'}}},
                {'Statement': [{'Effect': 'Allow', 'Action': check['policy'], 'Resource': '*'}]}
            ]),
            ('Events', OrderedDict([
                ('ScheduledCheck', OrderedDict([
                    ('Type', 'Schedule'),
                    ('Properties', OrderedDict([
                        ('Schedule', 'rate(6 hours)'),
                        ('Name', f"{check['name']}Schedule"),
                        ('Description', f"Runs the {check['desc']}"),
                        ('Enabled', True)
                    ]))
                ]))
            ]))
        ]))
    ])
    
    template['Outputs'][f"{func_name}Arn"] = OrderedDict([
        ('Description', f"ARN of the {check['name']} Lambda"),
        ('Value', {'Fn::GetAtt': [func_name, 'Arn']})
    ])

# Handle custom tags like !Ref and !GetAtt manually if PyYAML messes them up, but since they were parsed 
# by the SafeLoader, we might get dictionaries instead. Wait, let's fix Ref and GetAtt output just in case.
yaml.SafeDumper.add_representer(
    OrderedDict, 
    lambda dumper, data: dumper.represent_dict(data.items())
)

with open('template.yaml', 'w') as f:
    f.write("AWSTemplateFormatVersion: '2010-09-09'\n")
    f.write("Transform: AWS::Serverless-2016-10-31\n")
    yaml.dump(template, f, Dumper=Dumper, default_flow_style=False, sort_keys=False)
