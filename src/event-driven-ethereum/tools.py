import json


def retrieve_tasks(client_ssm, network):
    i = 0
    methods = client_ssm.get_parameters_by_path(Path=f'/ede/tasks/{network}/', Recursive=True)
    returnable_dict = dict()

    def update(position, task_dict):
        returnable_dict[position] = json.dumps(task_dict)

    for method in methods['Parameters']:
        ephemeral_dict = dict()
        task_name_list = method['Name'].split("/")[3:]
        keys = ["network", "contract_name", "task", "address"]
        key_index = 0
        for key in task_name_list:
            ephemeral_dict[keys[key_index]] = key
            key_index += 1

        ephemeral_dict['height'] = int(method['Value'])
        response = client_ssm.list_tags_for_resource(
            ResourceType='Parameter',
            ResourceId=method['Name']
        )

        for tag in response['TagList']:
            supported_services = ["SNS", "SQS", "DynamoDB"]
            for service in supported_services:
                if tag['Key'] == service:
                    if not tag['Key'] == "null":
                        ephemeral_dict[service] = tag['Value']
        i += 1
        update(i, ephemeral_dict)
    return returnable_dict



def update_block_height(client_ssm, event, height):
    client_ssm.put_parameter(
        Name=f'/ede/tasks/{event["network"]}/{event["contract_name"]}/{event["task"]}/{event["address"]}',
        Value=str(int(int(height)+int(1))),
        Type='String',
        Overwrite=True
    )


def retrieve_web3_endpoint(client_ssm, network) -> object:
    return client_ssm.get_parameter(Name=f'/ede/config/{network}')['Parameter']['Value']
