import boto3
ec2 = boto3.client('ec2')

def find_largest_ebs_volume():
    try:
        # Get all volumes
        response = ec2.describe_volumes()
        if 'Volumes' in response:
            largest_volume = None
            max_size = 0
            
            # Iterate through all volumes
            for volume in response['Volumes']:
                volume_size = volume['Size']  # The size of the volume in GiB
                if volume_size > max_size:
                    max_size = volume_size
                    largest_volume = volume
            
            # Display information about the largest volume
            result = ''
            if largest_volume:
                result += f"Largest EBS Volume:"
                result += f"Volume ID: {largest_volume['VolumeId']}"
                result += f"Size: {largest_volume['Size']} GiB"
                result += f"Type: {largest_volume['VolumeType']}"
                result += f"State: {largest_volume['State']}"
                return result 
            else:
                return "No volumes found."
        else:
            return "No volumes data received."
    except Exception as e:
        return f"An error occurred: {e}"

def find_smallest_ebs_volume():
    try:
        # Get all volumes
        response = ec2.describe_volumes()
        if 'Volumes' in response:
            smallest_volume = None
            min_size = float('inf')  # Initialize with infinity to ensure any real volume will be smaller
            
            # Iterate through all volumes
            for volume in response['Volumes']:
                volume_size = volume['Size']  # The size of the volume in GiB
                if volume_size < min_size:
                    min_size = volume_size
                    smallest_volume = volume
            
            # Display information about the smallest volume
            result = ''
            if smallest_volume:
                result += f"Smallest EBS Volume:"
                result += f"Volume ID: {smallest_volume['VolumeId']}"
                result += f"Size: {smallest_volume['Size']} GiB"
                result += f"Type: {smallest_volume['VolumeType']}"
                result += f"State: {smallest_volume['State']}"
                return result     
            else:
                return f"No volumes found."
        else:
             return  f"No volumes data received."
    except Exception as e:
        return f"An error occurred: {e}"
    
def calculate_total_ebs_volume_size():
   
    try:
        # Initialize total size
        total_size = 0
        
        # Get all volumes
        paginator = ec2.get_paginator('describe_volumes')
        page_iterator = paginator.paginate()

        # Iterate through all volumes and sum their sizes
        for page in page_iterator:
            for volume in page['Volumes']:
                total_size += volume['Size']  # Add the size of each volume to the total

        # Display the total size of all EBS volumes
        return f"Total EBS Volume Size: {total_size} GiB"
        
    except Exception as e:
        return f"An error occurred: {e}"
        
def count_volumes_by_type():

    volume_type_counts = {}

    try:
        # Get all volumes using a paginator to handle pagination automatically
        paginator = ec2.get_paginator('describe_volumes')
        page_iterator = paginator.paginate()

        # Iterate through each volume and track counts by volume type
        for page in page_iterator:
            for volume in page['Volumes']:
                volume_type = volume['VolumeType']
                if volume_type in volume_type_counts:
                    volume_type_counts[volume_type] += 1
                else:
                    volume_type_counts[volume_type] = 1

        # Display the counts of each volume type
        if volume_type_counts:
            result = f"EBS Volume Type Counts:"
            for volume_type, count in volume_type_counts.items():
                result += f"\n{volume_type}: {count}"
                
        else:
            return f"No EBS volumes found."
        return result         
    except Exception as e:
        return f"An error occurred: {e}"
        
def count_volumes_by_size():
    volume_size_counts = {}

    try:
        # Use a paginator to handle pagination automatically
        paginator = ec2.get_paginator('describe_volumes')
        page_iterator = paginator.paginate()

        # Iterate through each volume and count them by size
        for page in page_iterator:
            if 'Volumes' in page:
                for volume in page['Volumes']:
                    size = volume['Size']  # The size of the volume in GiB
                    if size in volume_size_counts:
                        volume_size_counts[size] += 1
                    else:
                        volume_size_counts[size] = 1

        # Display the counts of volumes by their size
        if volume_size_counts:
            result = f"EBS Volume Size Counts:"
            for size, count in sorted(volume_size_counts.items()):
                result += f"\n{size} GiB: {count}"
            return result         
        else:
            return f"No EBS volumes found."
                
    except Exception as e:
        return f"An error occurred: {e}"
        
def find_unattached_volumes():
    unattached_volumes = []

    try:
        # Use a paginator to handle pagination automatically
        paginator = ec2.get_paginator('describe_volumes')
        page_iterator = paginator.paginate(
            Filters=[{'Name': 'status', 'Values': ['available']}]
        )

        # Iterate through each volume and check if it is unattached
        for page in page_iterator:
            for volume in page['Volumes']:
                if not volume['Attachments']:  # If there are no attachments
                    unattached_volumes.append(volume['VolumeId'])

        # Display the IDs of all unattached volumes
        if unattached_volumes:
            result = f"Unattached EBS Volumes:"
            for volume_id in unattached_volumes:
                result += f"\n {volume_id} "
            return result         
        else:
            return f"No unattached EBS volumes found."

    except Exception as e:
        return f"An error occurred: {e}"
        
        
        