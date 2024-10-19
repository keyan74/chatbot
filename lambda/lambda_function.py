#Python code written by Karthikeyan Rajagopal 
#Purpose to use chat bot to manage the EC2 operational activities.

import json
import openai
import boto3
import os
import re
import botocore.exceptions
import S3details 
import EBSdetails
import securitygrp
from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta
from collections import defaultdict





# Function to generate the chatbot response using OpenAI's GPT-3
def generate_response(prompt: str) -> str | None:
    client = openai.Client()
    text: str | None = None
    choices = None
    try:
        response: Any = client.completions.create(
            model="gpt-3.5-turbo-instruct",
            prompt=prompt,
            temperature=0.7,
            max_tokens=200,
            top_p=1,
        )
        # print(response)
        choices: Any = response.choices[0]
        text = choices.text
        print(response.usage.model_dump())
    except Exception as e:
        print('ERROR:', e)
    return text.strip()



# Function to generate a chatbot response to the user's input
def chatbot_response(text):
    prompt = f"Using AWS SDK boto3 and ChatGPT, I received the following question: {text}."
    response = generate_response(prompt)
    return response


# Function to manage EC2 instances based on user input
def manage_ec2_instances(text):
    # Convert the input to lowercase and split into words
   words = text.lower().split()
   if 'list' in words and ('ec2' in words or 'instances' in words):
        # List EC2 instances
          instances = list_ec2_instances(0)
          return instances
   elif  ('get' in words or 'how' in words or 'many' in words) and ( 'ec2' in words and 'count' in words):
          instances = list_ec2_instances(1)
          return instances
   elif ('list' in words or 'get' in words) and ('on demand' in words):
          instances = get_on_demand_instances()
          return instances
   elif ('list' in words or 'get' in words or 'provide' in words ) and ('machines' in words and 'owned' in words):
           partial_owner_name = text.split()[-1] 
           details = fetch_instance_details_by_owner(partial_owner_name)
           
           if details:
               result = f"Instance ID                  IP Address               Instance Type             Launch date"
               for detail in details:
                  result += f"\n{detail['Instance ID']}          {detail['Private IP Address']}            {detail['Instance Type']}             {detail['Launch Date']}"
           else:
                  result = "No instances found for the given  owner"
           return result
   elif ('get' in words or 'list'in words or 'provide') and ('alerts' in words):
        
        cost_optimization_results = get_trusted_advisor_cost_optimization_checks()
        if cost_optimization_results:
            response = ''   
            for result in cost_optimization_results:
                response += f"Check Name: {result['Check Name']}\n"
                response += f"Status: {result['Status']}\n" 
                response +=f"Flagged Resources: {result['Flagged Resources']}\n"
                response +='---\n'
        else:
             response += "No cost optimization checks with flagged resources found."
        return response         
   
   elif ('get' in words) and ('instance' in words and  'type' in words and 'count' in words):
            counts = get_instance_type_counts()
            result = ''
            for instance_type, count in counts.items():
                result += f"\nInstance Type: {instance_type}, Count: {count}"
            return result
   elif ('get' in words and 'running' in words and 'count' in words  ) and ('ec2' in words or 'instance' in words):
            result = count_instances('R')
            return result
   elif ('get' in words and 'stopped' in words and 'count' in words  ) and ('ec2' in words or 'instance' in words):
            result = count_instances('S')
            return result
   elif ('get' in words and 'snapshot' in words and 'count' in words):
            result = count_aws_resources('S')
            return result
   elif ('get' in words and 'ebs' in words and 'count' in words):
            result = count_aws_resources('E')
            return result
   elif ('get' in words and 'ami' in words and 'count' in words):   
            result = count_aws_resources('A')
            return result
   elif ('add' in words and 'tag' in words):
            result  = tag_all_ec2_instances(text)
            return result 
   elif ('remove' in words and 'tag' in words):
            result = remove_ec2_tag(text)
            return result
   elif ('get' in words and 'billing' in words and 'instancetype' not in words):
        year, month_name = extract_year_month(text)
        if year and month_name:
              # Get AWS billing for the extracted year and month
          year_flg = 0
          result = get_aws_billing(year, month_name,year_flg)
          return result
        elif year:
          year_flg = 1
          result = get_aws_billing(year, month_name,year_flg)    
          return result
        else:
           return "Input value is not proper."
   elif ('provide' in words or 'get' in words or 'list' in words)  and ('underutilized' in words ):
         underutilized_instances = get_trusted_advisor_underutilized_ec2()
         result = '' 
         for instance_metadata in underutilized_instances:
           instance_id = instance_metadata[1]
           owner_name = get_instance_details(instance_id)
           cpu_utilization = get_cpu_under_utilization(instance_id)
           result +=f"Instance ID: {instance_id}\n"
           result +=f"Instance Type: {instance_metadata[3]}\n"
           result +=f"Estimated Monthly Savings: {instance_metadata[4]}\n"
           result +=f"CPU Utilization 14-Day Average: {cpu_utilization}%\n"
           result +=f"Number of Days Low Utilization: {instance_metadata[21]}\n"
           result +=f"Owner Name: {owner_name}\n"
           result +="---\n"
         return result
           
   elif ('get' in words or 'find' in words) and ('cpu' in words or 'utilization' in words):
         ip_address = find_ip_addresses(text)
         if ip_address:
             instance_id = get_instance_id_from_ip(ip_address[0])
             if instance_id:
                cpu_stats = get_cpu_utilization(instance_id)
                if cpu_stats['Datapoints']:
                       result = ''
                       for point in cpu_stats['Datapoints']:
                         cpu_avg = round(point['Average'], 2)
                         result += f"\nMonth: {point['Timestamp'].strftime('%Y-%m')}, CPU Utilization: {cpu_avg}%n"
                       return result        
                else:
                   return "No stats available for the given instance ID"
             else:
                return f"No instance mapped with this IP address"
         else:
              return f"Inavlid IP address"
   elif ('list' in words and 'spot' in words):
        result =  fetch_spot_instance_details()
        if result:
            return result
        else:
            return f"No spot instance details found"
   elif 'start' in words and ('instance' in words or 'ec2' in words):
        # Start an EC2 instance
        instance_id = extract_instance_id(text)
        if instance_id:
            return start_instance(instance_id)

   elif 'stop' in words and ('instance' in words or 'ec2' in words):
        # Stop an EC2 instance
        instance_id = extract_instance_id(text)
        if instance_id:
            return stop_instance(instance_id)
   elif ('created' in words and 'instances' in words):
        result =  filter_instances_by_time(text)
        return result 
   elif ('get' in words and 'instancetype' in words and 'billing' in words):
        result = get_monthly_billing_by_instance_type(words[5],words[4])
        return result 
   elif ('s3' in words and 'buckets' in words and 'list' in words):
         response = S3details.list_s3_buckets()
         return response
   elif ('s3' in words and 'bucket' in words and 'size' in words):
         response = S3details.s3_bucket_sizes(text)
         if response:
             return response
         else:
             return "Bucket is not found"
   elif ('s3' in words and 'create' in words and 'bucket' in words):
        response =  S3details.create_s3_bucket(words[3])
        return response
   elif ('s3' in words and 'drop' in words and 'bucket' in words):
        response =  S3details.delete_s3_bucket(words[3])        
        return response
   elif ('s3' in words and 'list' in words and 'files'):
        response = S3details.list_files_in_bucket(words[5])
        return response 
   elif ('find' in words and 'maximum' in words and 'volume' in words ):
       response = EBSdetails.find_largest_ebs_volume()
       return response
   elif ('find' in words and 'minimum' in words and 'volume' in words ):
       response = EBSdetails.find_smallest_ebs_volume()
       return response
   elif ('find' in words and 'total' in words and 'volume' in words ):
       response = EBSdetails.calculate_total_ebs_volume_size()
       return response       
   elif ('find' in words and 'type' in words and 'volume' in words and 'count' in words ):
       response = EBSdetails.count_volumes_by_type()
       return response       
   elif ('find' in words and 'size' in words and 'volume' in words and 'count' in words ):
       response = EBSdetails.count_volumes_by_size()
       return response       
   elif ('find' in words and 'unattached' in words and 'volumes' in words ):
        
       response = EBSdetails.find_unattached_volumes()
       return response
   elif ('get' in words and 'stopped' in words and 'months' in words ):
         
          stopped_instances = get_long_stopped_instances(words[5])

           # Print the details in a column-row format
          result = '' 
          if stopped_instances:
               
               result  = f"Instance ID"  "Private IP" "Instance Name" "Owner" "Stopped Date\n"

               for instance in stopped_instances:
                 result += f"{instance['Instance ID']} {instance['Private IP']} {instance['Instance Name']} {instance['Owner']} {instance['Stopped Date']}\n"
                 response = result
          else:
              response = f"No instances found that have been stopped for more than {months} months."
          return response
   elif ('add' in words or 'remove' in words) and ('security' in words and 'group' in words):
           ip_addresses_input = words[5]
           response = securitygrp.modify_security_group(words[0],words[3],ip_addresses_input)    
           return response 
   elif ('get' in words and 'table' in words and 'metadata' in words):
         str_spl = text.split()
         table_name = str_spl[3]
         columns, item_count = get_table_metadata(table_name)
         result = ''
         if columns is not None:
                 result = f"Table Name: {table_name}\n"
                 result += f"Columns and Data Types:\n"
                 for column_name, data_type in columns.items():
                      result += f" - {column_name}: {data_type}\n"
                 result += f"Number of Records: {item_count}"
         else:
              result = f"Failed to fetch table metadata."
         return result
   
   elif ('list' in words and 'dynamodb' in words and 'tables' in words):
      result = '' 
      tables = list_dynamodb_tables()
      if tables:
        for table in tables:
            result += f"\n {table}"
      else:
        result = 'No tables found'
      #print(result)        
      return result         
   else:
        # Generate a response using OpenAI's GPT-3
        return chatbot_response(text)


def extract_year_month(input_string):
    # Regular expression to find the month name and year in the input string
    match = re.search(r'\bfor the month (\w+) (\d{4})', input_string)
   
    if not match:
         match = re.search(r'\bfor the year (\d{4})', input_string)
         
         if match:
            year = int(match.group(1))
            return year, None
         else:
            return None, None
    else: 
        
        month_name = match.group(1)
        year = int(match.group(2))
        return year, month_name

def tag_all_ec2_instances(input_string):
    
    tag_input     = input_string[len("add tag "):]
    # Extract tag key and value from the predefined input string
    try:
        tag_key, tag_value = tag_input.split(":")
        
    except ValueError:
        return f"Invalid input format. The tag input should be in the format 'key:value'."
        
    ec2_client = boto3.client('ec2')    
    response = ec2_client.describe_instances()
    instance_ids = []
    tot_count = 0
    for reservation in response['Reservations']:
        for instance in reservation['Instances']:
            instance_ids.append(instance['InstanceId'])
            tot_count += 1
    # Pagination check: Continue retrieving instances if a NextToken is present
    while response.get('NextToken') is not None:
        response = ec2.describe_instances(NextToken=response['NextToken'])
        for reservation in response['Reservations']:
            for instance in reservation['Instances']:
                instance_ids.append(instance['InstanceId'])
                tot_count += 1
    # Check if there are any instances to tag
    if instance_ids:
        # Add the specified tag to all instances
        ec2_client.create_tags(Resources=instance_ids, Tags=[{'Key': tag_key, 'Value': tag_value}])
        return f"Tags added to {tot_count} instances"
    else:
         return f"No instances found in the account."
         
def remove_ec2_tag(input_string):
    # Check if the input format is correct
    if not input_string.startswith("remove tag "):
         return f"Invalid input format. Expected format is 'remove tag <tagname>'."
        

    # Extract the tag name to be removed
    tag_name = input_string[len("remove tag "):].strip()
    
    if not tag_name:
         return f"No tag name provided. Please specify a tag name to remove."
      


    # List all instances
    ec2_client = boto3.client('ec2')    
    response = ec2_client.describe_instances()
    tag_count = 0
    for reservation in response['Reservations']:
        for instance in reservation['Instances']:
            instance_id = instance['InstanceId']
            tag_count += 1
         #Attempt to remove the specified tag from this instance
            try:
                ec2_client.delete_tags(
                    Resources=[instance_id],
                    Tags=[
                        {'Key': tag_name}
                    ]
                )
            #    print(f"Attempted to remove tag '{tag_name}' from instance {instance_id}.")
            except Exception as e:
                skip

    # Handle pagination
    while response.get('NextToken') is not None:
        response = ec2_client.describe_instances(NextToken=response['NextToken'])
        for reservation in response['Reservations']:
            for instance in reservation['Instances']:
                instance_id = instance['InstanceId']
                tag_count += 1
                try:
                    ec2_client.delete_tags(
                        Resources=[instance_id],
                        Tags=[
                            {'Key': tag_name}
                        ]
                    )
                    #print(f"Attempted to remove tag '{tag_name}' from instance {instance_id}.")
                except Exception as e:
                    skip 
    if tag_count > 0:
         return f"Tags removed from {tag_count} instances"
    else:
         return f"No instances found for this account"

def count_instances(status_code):
    
    if status_code == 'R':
        instances = ec2.instances.filter(Filters=[{'Name': 'instance-state-name', 'Values': ['running']}])
    elif status_code == 'S':
        instances = ec2.instances.filter(Filters=[{'Name': 'instance-state-name', 'Values': ['stopped']}])

    # Count the instances
    instance_count = sum(1 for _ in instances)

    # Print the result
    state = "running" if status_code == 'R' else "stopped"
    result = f"Count of {state} instances: {instance_count}"
    return result 
    
def fetch_spot_instance_details():
    instances_details = []
    # Fetch all instances
    response = ec2.instances.filter(
        Filters=[
            {
                'Name': 'instance-lifecycle',
                'Values': ['spot']
            }
        ]
    )

    result = f"     Instance ID             Instance Type          Owner"
      # Iterate over reservations and instances to extract details
    for instance in response:
       if instance.tags:
            for tag in instance.tags:
                if tag['Key'].lower() == 'owner':
                    owner_tag_value = tag['Value']
                    break
       instance_detail = {
            'Instance ID': instance.id,
            'Owner': owner_tag_value,
            'Instance Type': instance.instance_type
            }
       instances_details.append(instance_detail)    
    for detail in instances_details:
         result += f"\n{detail['Instance ID']}        {detail['Instance Type']}         {detail['Owner']}"
    return result     
    
def get_trusted_advisor_underutilized_ec2():
    client = boto3.client('support')
    checks = client.describe_trusted_advisor_checks(language='en')['checks']
    check_id = next((check['id'] for check in checks if check['name'] == "Low Utilization Amazon EC2 Instances"), None)
    
    if check_id:
        result = client.describe_trusted_advisor_check_result(checkId=check_id, language='en')['result']
        return [res['metadata'] for res in result['flaggedResources'] if res['status'] != 'ok']
    else:
        return []

def count_aws_resources(resource_type):
    ec2_client = boto3.client('ec2') 
    if resource_type == 'A':
        amis = ec2_client.describe_images(Owners=['self'])
        result = f"Count of AMIs: {len(amis['Images'])}"
    elif resource_type == 'S':
        snapshots =ec2_client.describe_snapshots(OwnerIds=['self'])
        result = f"Count of Snapshots: {len(snapshots['Snapshots'])}"
    elif resource_type == 'E':
        volumes = ec2_client.describe_volumes()
        result = f"Count of EBS Volumes: {len(volumes['Volumes'])}"
    return result

def get_instance_details(instance_id):
    try:
      instance = ec2.Instance(instance_id)
      tags = {tag['Key'].lower(): tag['Value'] for tag in instance.tags or [] if 'Key' in tag}
      owner_name = tags.get('owner', 'Unknown')   # Adjust 'Owner' if you use a different tag key for the owner's name
      return owner_name
    except ec2.exceptions.ClientError as e:
       if e.response['Error']['Code'] == 'InvalidInstanceID.NotFound':
          print(f"The instance ID {instance_id} does not exist in this region.")
          return 
       else:
        # Handle other possible exceptions
         print(e.response['Error']['Message'])
         return


def get_cpu_under_utilization(instance_id):
    cloudwatch = boto3.client('cloudwatch')
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(days=14)
   
    metrics = cloudwatch.get_metric_statistics(
        Namespace='AWS/EC2',
        MetricName='CPUUtilization',
        Dimensions=[{'Name': 'InstanceId', 'Value': instance_id}],
        StartTime=start_time,
        EndTime=end_time,
        Period=3600 * 24,  # daily statistics
        Statistics=['Average']
    )
    average_cpu = sum(data_point['Average'] for data_point in metrics['Datapoints']) / len(metrics['Datapoints']) if metrics['Datapoints'] else 0
    return round(average_cpu, 2)

def get_aws_billing(year, month_name,year_flg):
    # Initialize Cost Explorer client
    client = boto3.client('ce')
    
    if year_flg == 0: # Convert month name to month number
      if len(month_name) == 3:
        datetime_object = datetime.strptime(month_name, "%b")
      else:
        datetime_object = datetime.strptime(month_name, "%B")  
    
      month = datetime_object.month
      out_val = ''    
    # Format start and end dates for the given month and year
      start_date = f"{year}-{month:02d}-01"
      if month == 12:
         end_date = f"{year+1}-01-01"
      else:
        end_date = f"{year}-{month+1:02d}-01"
      
      response = client.get_cost_and_usage(
          TimePeriod={'Start': start_date, 'End': end_date},
          Granularity='MONTHLY',
          Metrics=["UnblendedCost"])
      
      for result in response['ResultsByTime']:
           
            start = result['TimePeriod']['Start']
            end = result['TimePeriod']['End']
            amount = round(float(result['Total']['UnblendedCost']['Amount']), 2)  # Rounded here
            unit = result['Total']['UnblendedCost']['Unit']
            out_val  += f"Cost from {start} to {end}: {amount} {unit}" 
            
      return out_val      
    else:
      out_val = ''
      try:  
        for month in range(1, 13):
          start_date = datetime(year, month, 1).strftime('%Y-%m-%d')
         
        # Handle December as a special case to roll over to the next year
          if month == 12:
            end_date = datetime(year + 1, 1, 1).strftime('%Y-%m-%d')
          else:
            end_date = datetime(year, month + 1, 1).strftime('%Y-%m-%d')   
             
          response = client.get_cost_and_usage(
          TimePeriod={'Start': start_date, 'End': end_date},
          Granularity='MONTHLY',
          Metrics=["UnblendedCost"])

          for result in response['ResultsByTime']:
            start = result['TimePeriod']['Start']
            end = result['TimePeriod']['End']
            amount = round(float(result['Total']['UnblendedCost']['Amount']), 2)  # Rounded here
            unit = result['Total']['UnblendedCost']['Unit']
            out_val  += f"\nCost from {start} to {end}: {amount} {unit}" 
        return out_val        
      except Exception as e:
         None      
         
def get_trusted_advisor_cost_optimization_checks():
    client = boto3.client('support')  # Trusted Advisor API calls must be made to the 'us-east-1' region
    # Retrieve all Trusted Advisor checks
    response = client.describe_trusted_advisor_checks(language='en')
    
    # Filter for cost optimization checks
    cost_checks = [check for check in response['checks'] if check['category'] == 'cost_optimizing']
    
    # Store the results
    results = []

    # Iterate through cost optimization checks and get their status
    for check in cost_checks:
        check_id = check['id']
        check_name = check['name']
        
        # Get check result (status and flagged resources)
        check_result = client.describe_trusted_advisor_check_result(checkId=check_id, language='en')
        result_summary = check_result['result']
        
        # Safely get the status summary and flagged resources
        status_summary = result_summary.get('status', 'N/A')
        flagged_resources = result_summary.get('flaggedResources', [])
        
        # Use the length of flagged_resources if it exists, or set to 0
        flagged_resources_count = len(flagged_resources) if flagged_resources else 0
        
        # Include the check only if flagged_resources_count > 0
        if flagged_resources_count > 0:
            results.append({
                'Check Name': check_name,
                'Status': status_summary,
                'Flagged Resources': flagged_resources_count
            })
    
    return results
         
def fetch_instance_details_by_owner(partial_owner_name):
    # Fetch all instances
    instances = ec2.instances.all()
    global owner_name
    owner_name = ''     
    # Filter instances by partial owner name match
    matched_instances = []
    for instance in instances:
        for tag in instance.tags or []:
            if tag['Key'] == 'Owner' and partial_owner_name.lower() in tag['Value'].lower():
                matched_instances.append(instance)
                owner_name = tag['Value'].lower()
                break
    
    # Collect details of matched instances
    instance_details = []
    for instance in matched_instances:
        instance_name = next((tag['Value'] for tag in instance.tags or [] if tag['Key'] == 'Name'), None)
        
        details = {
            'Instance ID': instance.id,
            'Private IP Address': instance.private_ip_address,
            'Instance Type': instance.instance_type,
            'Instance Name': instance_name,
            'Launch Date': instance.launch_time.strftime('%Y-%m-%d %H:%M:%S') }
        instance_details.append(details)
    
    return instance_details
         
def get_instance_type_counts():
    
    # Initialize a dictionary to hold instance type counts
    instance_type_counts = {}
    # Iterate over all instances
    for instance in ec2.instances.all():
        # Get the instance type
        instance_type = instance.instance_type
        # Count the instance types
        if instance_type in instance_type_counts:
            instance_type_counts[instance_type] += 1
        else:
            instance_type_counts[instance_type] = 1
            
    return instance_type_counts  
    
def find_ip_addresses(input_string):
    # Regular expression for matching IPv4 addresses
    ipv4_pattern = r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'
    ipv4_addresses = re.findall(ipv4_pattern, input_string)
    return ipv4_addresses

# Example input string

def get_instance_id_from_ip(ip_address):
    filters = [{'Name': 'private-ip-address', 'Values': [ip_address]}]
    instances = ec2.instances.filter(Filters=filters)
    for instance in instances:
        return instance.id  
    return None

def get_cpu_utilization(instance_id):
    start_date = datetime.now() - timedelta(days=365)  # last year
    end_date = datetime.now()
   
    stats = cloudwatch.get_metric_statistics(
        Namespace='AWS/EC2',
        MetricName='CPUUtilization',
        Dimensions=[{'Name': 'InstanceId', 'Value': instance_id}],
        StartTime=start_date,
        EndTime=end_date,
        Period=2592000,  # Monthly period in seconds
        Statistics=['Average']
    )
    return stats 


# Function to list EC2 instances
def list_ec2_instances(cnt_flag):
    total_instances = 0
    instances = ec2.instances.filter(Filters=[{'Name': 'instance-state-name', 'Values': ['running', 'stopped']}])
    result = "Instance ID | State | Type"
    for instance in instances:
         total_instances += 1
         result += f"\n{instance.id} | {instance.state['Name']} | {instance.instance_type}"
    if cnt_flag == 1:    
        return f"Total instance count is {total_instances}"
    else:
        return result 


# Function to start an EC2 instance
def start_instance(instance_id):
   try:    
     instance = ec2.Instance(instance_id)
     if instance.state['Name'] == 'stopped':
        instance.start()
        return f"Starting instance {instance_id}."
     else:
        return f"Instance {instance_id} is already running."
   except Exception as e:
         return f"Error: {e}"     

# Function to stop an EC2 instance
def stop_instance(instance_id):
    instance = ec2.Instance(instance_id)
    if instance.state['Name'] == 'running':
        instance.stop()
        return f"Stopping instance {instance_id}."
    else:
        return f"Instance {instance_id} is already stopped."

# Function to get on demand instances
def get_on_demand_instances():

    tag_key = 'iNeedNonSpot'
    tag_value = 'True'
    filters = [
        {
            'Name': 'tag:' + tag_key,
            'Values': [tag_value]
        }]
    
    result = "Instance ID | Owner | Type"
    for instance in ec2.instances.filter(Filters=filters):
        instance_id = instance.id  # Corrected from instance['InstanceId'] to instance.id
        instance_type = instance.instance_type  # Corrected from instance['InstanceType'] to instance.instance_type
        
        # Corrected tag access method
        instance_name = next((tag['Value'] for tag in instance.tags or [] if tag['Key'] == 'Name'), 'N/A')
        instance_owner = next((tag['Value'] for tag in instance.tags or [] if tag['Key'] == 'Owner'), 'N/A')
        
        result += f"\n{instance_id} | {instance_owner} | {instance_type}"
    
    return result 
        
# Function to extract the instance ID from the user's input
def extract_instance_id(response):
    words = response.split(' ')
    for word in words:
        if word.startswith('i-'):
            return word
    return None

# Function to find the list of instance whcih was created on a giveb period
def get_instance_creation_events(start_date, end_date):
    
    cloudtrail = boto3.client('cloudtrail')

    # Format dates for API call
    start_date = start_date.isoformat()
    end_date = end_date.isoformat()

    response = cloudtrail.lookup_events(
        LookupAttributes=[{'AttributeKey': 'EventName', 'AttributeValue': 'RunInstances'}],
        StartTime=start_date,
        EndTime=end_date,
    )

    instances_creation_time = {}

    for event in response['Events']:
        event_time = event['EventTime']
        event_data = json.loads(event['CloudTrailEvent'])

        if event_data.get('responseElements') and 'instancesSet' in event_data['responseElements']:
            for item in event_data['responseElements']['instancesSet']['items']:
                instance_id = item['instanceId']
                instances_creation_time[instance_id] = event_time

    return instances_creation_time

def fetch_instance_details(instance_ids):
    ec2 = boto3.client('ec2')
    instance_details = []

    for instance_id in instance_ids:
        try:
            response = ec2.describe_instances(InstanceIds=[instance_id])
            for reservation in response['Reservations']:
                for instance in reservation['Instances']:
                    owner_tag_value = next((tag['Value'] for tag in instance.get('Tags', []) if tag['Key'].lower() == 'owner'), 'No owner tag')
                    instance_details.append({
                        'Instance ID': instance['InstanceId'],
                        'Instance Type': instance['InstanceType'],
                        'Launch Time': instance['LaunchTime'],
                        'Owner': owner_tag_value
                    })
        except botocore.exceptions.ClientError as error:
            if error.response['Error']['Code'] == 'InvalidInstanceID.NotFound':
                None
            else:
                print(f"An error occurred for instance ID {instance_id}: {error.response['Error']['Message']}")

    return instance_details

def filter_instances_by_time(input_time):
    now = datetime.now()
    if 'hour' in input_time:
        value = int(re.sub('[^0-9]', '', input_time))
        start_time = now - timedelta(hours=value)
    elif 'week' in input_time:
        value = int(re.sub('[^0-9]', '', input_time))
        start_time = now - timedelta(weeks=value)
    elif 'month' in input_time:
        value = int(re.sub('[^0-9]', '', input_time))
        start_time = now - relativedelta(months=value)
    else:
        result = "Invalid input format. Please enter a time period like '24 hours', '1 week', or '3 months'."
        return result

    instances_creation_time = get_instance_creation_events(start_time, now)
    result = '' 
    # Fetch details for instances created in the specified time frame
    if instances_creation_time:
        instance_details = fetch_instance_details(list(instances_creation_time.keys()))
        result = f"Instance ID               Instance Type               Creation Date                   Owner"
        for detail in instance_details:
            creation_date = instances_creation_time[detail['Instance ID']].date()
            result += f"\n{detail['Instance ID']}       {detail['Instance Type']}                      {creation_date}                    {detail['Owner']}"
                   
    else:
        result = "No instances were created in the specified time frame."
    return result
    
def get_user_specified_month(year, month):
    """ Utility to get the start and end date of a user-specified month. """
    year = int(year)
    month = int(month)
    start_date = datetime(year, month, 1)
   
    if month == 12:
        end_date = datetime(year + 1, 1, 1) - timedelta(days=1)
    else:
        end_date = datetime(year, month + 1, 1) - timedelta(days=1)
       
    return start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')

def get_monthly_billing_by_instance_type(year,month):
    client = boto3.client('ce')

    start_date, end_date = get_user_specified_month(year, month)
  
    try:
        response = client.get_cost_and_usage(
            TimePeriod={
                'Start': start_date,
                'End': end_date
            },
            Granularity='MONTHLY',
            Metrics=["UnblendedCost"],
            GroupBy=[
                {
                    'Type': 'DIMENSION',
                    'Key': 'INSTANCE_TYPE'
                }
            ]
        )

        # Organize data by instance type
        data = {}
       
        for result in response['ResultsByTime']:
            for group in result['Groups']:
                instance_type = group['Keys'][0]
                cost = float(group['Metrics']['UnblendedCost']['Amount'])
                data[instance_type] = cost
        
        
        result = f"Cost Report for {datetime(int(year), int(month), 1).strftime('%B %Y')}:\n"
        result += "\n{:<20} {:<15}".format("Instance Type", "Cost (USD)")
  
        
        for instance_type, cost in data.items():
            if instance_type == 'NoInstanceType':
               instance_type = 'Totalcosts'
            result += "\n{:<20} ${:<15.2f}".format(instance_type, cost)
        return result 
    except Exception as e:
         return f"An error occurred: {e}"

def list_dynamodb_tables():
    try:
        # List tables with pagination
        dynamodb_client = boto3.client('dynamodb')
        response = dynamodb_client.list_tables()
        table_names = response.get('TableNames', [])
        while 'LastEvaluatedTableName' in response:
            response = dynamodb_client.list_tables(ExclusiveStartTableName=response['LastEvaluatedTableName'])
            table_names.extend(response.get('TableNames', []))
        return table_names
    except Exception as e:
        print(f"Error listing tables: {e}")
        return []
        
def get_table_metadata(table_name):
    # Get the table
    dynamodb = boto3.resource('dynamodb')
    dynamodb_client = boto3.client('dynamodb')
    table = dynamodb.Table(table_name)
    
   
    # Fetch table description to get the item count
    try:
       
        table_description = dynamodb_client.describe_table(TableName=table_name)
        item_count = table_description['Table']['ItemCount']
    except Exception as e:
        print(f"Error fetching table description for table {table_name}: {e}")
        return None, None

    # Scan the table to get all items
    try:
        scan_response = table.scan()
        items = scan_response['Items']

        # Continue scanning if there are more items
        while 'LastEvaluatedKey' in scan_response:
            scan_response = table.scan(ExclusiveStartKey=scan_response['LastEvaluatedKey'])
            items.extend(scan_response['Items'])

        # Collect attributes and their types
        attributes = defaultdict(set)
        for item in items:
            for key, value in item.items():
                attributes[key].add(type(value).__name__)

        # Convert sets to a string of types
        attributes = {key: ', '.join(types) for key, types in attributes.items()}

        return attributes, item_count

    except Exception as e:
        print(f"Error scanning table {table_name}: {e}")
        return None, None

def get_long_stopped_instances(months):
    # Calculate the threshold date
    client = boto3.client('ec2')
    months = int(months)
    threshold_date = datetime.now() - timedelta(days=30*months)
    
    # Filter for stopped instances
    instances = ec2.instances.filter(
        Filters=[
            {'Name': 'instance-state-name', 'Values': ['stopped']}
        ]
    )
    
    stopped_instances = []

    for instance in instances:
        instance_details = client.describe_instances(InstanceIds=[instance.id])
        reservations = instance_details['Reservations'][0]['Instances'][0]
        
        # Get the stopped date from the state transition reason
        state_transition_reason = reservations.get('StateTransitionReason', '')
        if 'User initiated' in state_transition_reason:
            stop_time_str = state_transition_reason.split('(')[-1][:-1]
            stop_time = datetime.strptime(stop_time_str, '%Y-%m-%d %H:%M:%S GMT')
        else:
            stop_time = None

        if stop_time and stop_time < threshold_date:
            instance_id = instance.id
            private_ip = reservations.get('PrivateIpAddress', 'N/A')
            tags = {tag['Key']: tag['Value'] for tag in reservations.get('Tags', [])} if reservations.get('Tags') else {}
            instance_name = tags.get('Name', 'N/A')
            owner = tags.get('Owner', 'N/A')
            stopped_instance = {
                'Instance ID': instance_id,
                'Private IP': private_ip,
                'Instance Name': instance_name,
                'Owner': owner,
                'Stopped Date': stop_time.strftime('%Y-%m-%d %H:%M:%S')
            }
            stopped_instances.append(stopped_instance)

    return stopped_instances

# Create an EC2 resource using the boto3 library
ec2 = boto3.resource('ec2')
cloudwatch = boto3.client('cloudwatch')


#Test the manage_ec2_instances function
#user_input = 'find the instances created in the last 4 months'
#response = manage_ec2_instances(user_input)
#print(response)

# AWS Lambda function handler
def lambda_handler(event, context):
   
  
  user_input = event.get('user_input', '')
  
  if user_input:
        # Generate a chatbot response based on the user's input
        response = manage_ec2_instances(user_input)
        return {
            'statusCode': 200,
            'body': json.dumps({
                'response': response
            })
        }
  else:
        return {
            'statusCode': 400,
            'body': json.dumps({
                'error': 'No user inputs provided.'
            })
        }