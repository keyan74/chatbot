import boto3
import re
from botocore.exceptions import ClientError

s3 = boto3.client('s3')

def list_s3_buckets():
    # Call S3 to list current buckets
    response = s3.list_buckets()
       # Get a list of all bucket names from the response
    buckets = [bucket['Name'] for bucket in response['Buckets']]
    # Print out the bucket list
    result = "Bucket List:"
    for bucket in buckets:
        result += f"\n {bucket}"
    return result
    
def s3_bucket_sizes(text):
    size = 0
    before_word = 'bucket'
    after_word = 'size'
    pattern = rf"\b{before_word}\s+([\w-]+)\s+{after_word}\b"
    # Searching the text
    match = re.search(pattern, text)
    # Returning the found word if there's a match
    if match:
       bucket_name =  match.group(1)  
       # List objects within the bucket
       paginator = s3.get_paginator('list_objects_v2')
       for page in paginator.paginate(Bucket=bucket_name):
          if "Contents" in page:  # Check if the page has contents
            for obj in page['Contents']:
                size += obj['Size']
                result = f"{bucket_name}: {size / 1024 / 1024:.2f} MB"

    return result 
    
def create_s3_bucket(bucket_name):
    try:
        s3.create_bucket(Bucket=bucket_name)
        result = f"Bucket '{bucket_name}' created successfully."
        return result
    except ClientError as e:
         result = f"Failed to create bucket: {e}"
         return result 

def delete_s3_bucket(bucket_name):
    try:
        s3.delete_bucket(Bucket=bucket_name)
        result = f"Bucket '{bucket_name}' deleted successfully."
        return result 
    except ClientError as e:
         result = f"Failed to delete bucket: {e}"
         return result 

def list_files_in_bucket(bucket_name):
 
    paginator = s3.get_paginator('list_objects_v2')

    try:
        # Create a reusable Paginator for listing the objects
        page_iterator = paginator.paginate(Bucket=bucket_name)
        
        result = f"Files in bucket '{bucket_name}':"
        for page in page_iterator:
            if 'Contents' in page:
                for obj in page['Contents']:
                     result += f"\n {obj['Key']} "
            else:
                break
        return result     
    except boto3.exceptions.S3UploadFailedError as e:
         return f"Failed to access bucket '{bucket_name}'. Error: {e}"
    except Exception as e:
         return f"An error occurred: {e}"
