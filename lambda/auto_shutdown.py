import boto3

def lambda_handler(event, context):
    ec2 = boto3.client("ec2", region_name="us-east-1")

    response = ec2.describe_instances(
        Filters=[
            {
                "Name": "instance-state-name",
                "Values": ["running"]
            }
        ]
    )

    stopped = []
    skipped = []

    for reservation in response["Reservations"]:
        for instance in reservation["Instances"]:
            instance_id = instance["InstanceId"]

            tags = {
                tag["Key"]: tag["Value"]
                for tag in instance.get("Tags", [])
            }

            if tags.get("KeepRunning") == "true":
                print(f"Skipping {instance_id} - {tags.get('Name', 'unnamed')} (KeepRunning=true)")
                skipped.append(instance_id)
            else:
                print(f"Stopping {instance_id} - {tags.get('Name', 'unnamed')}")
                ec2.stop_instances(InstanceIds=[instance_id])
                stopped.append(instance_id)

    print(f"Summary: stopped {len(stopped)}, skipped {len(skipped)}")

    return {
        "statusCode": 200,
        "body": f"Stopped: {stopped}, Skipped: {skipped}"
    }
