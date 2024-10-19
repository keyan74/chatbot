import boto3
ec2 = boto3.client('ec2')

def modify_security_group(action, security_group_id, ip_addresses):
    if action not in ['add', 'remove']:
        raise ValueError("Action must be 'add' or 'remove'")
    if isinstance(ip_addresses, str):
        ip_addresses = [ip_addresses] if ',' not in ip_addresses else ip_addresses.split(',')

    for ip in ip_addresses:
       
        try:
            # Find the instance ID based on the given IP address
            response = ec2.describe_instances(
                Filters=[
                    {'Name': 'private-ip-address', 'Values': [ip]}
                ]
            )

            instances = response['Reservations']
            if not instances:
                print(f"No instance found with IP address: {ip}")
                continue
            result = '' 
            for reservation in instances:
                for instance in reservation['Instances']:
                    instance_id = instance['InstanceId']
                    current_groups = [sg['GroupId'] for sg in instance['SecurityGroups']]

                    if action == 'add':
                        if security_group_id not in current_groups:
                            new_groups = current_groups + [security_group_id]
                            ec2.modify_instance_attribute(
                                InstanceId=instance_id,
                                Groups=new_groups
                            )
                            result += f"\nAdded security group {security_group_id} to instance {instance_id} with IP {ip}"
                        else:
                            result += f"\nSecurity group {security_group_id} is already attached to instance {instance_id} with IP {ip}"

                    elif action == 'remove':
                        if security_group_id in current_groups:
                            new_groups = [sg for sg in current_groups if sg != security_group_id]
                            ec2.modify_instance_attribute(
                                InstanceId=instance_id,
                                Groups=new_groups
                            )
                            result += f"\nRemoved security group {security_group_id} from instance {instance_id} with IP {ip}"
                        else:
                           result += f"\nSecurity group {security_group_id} is not attached to instance {instance_id} with IP {ip}"
                    return result
        except Exception as e:
           result +=f"Error modifying security group for instance with IP {ip}: {str(e)}"
           return result
