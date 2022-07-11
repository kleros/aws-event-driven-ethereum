import boto3
from web3 import Web3
import json
import os
import datetime

REGION = os.environ.get("REGION")
client = boto3.client('ssm', region_name=REGION)

paginator = client.get_paginator('get_parameters_by_path')


def retrieve_tasks():
    return client.get_parameters_by_path(Path=f'/ede/tasks/', Recursive=True)


def retrieve_stats():
    returnable = dict()
    returnable["last-updated"] = datetime.datetime.now().isoformat()
    return returnable


def retrieve_networks():
    networks =  client.get_parameters_by_path(Path=f'/ede/config/', Recursive=True)
    network_d = dict()
    for parameter in networks["Parameters"]:
        trimmed_network = str(parameter["Name"]).split("/")[3]
        rpc = parameter["Value"]
        network_d[trimmed_network] =  rpc
    return network_d


def suggested_threshold():
    return 300


def lambda_entrypoint(event, context):
    networks = retrieve_networks()
    applications = retrieve_tasks()

    content = {}
    network_stats = {}
    alarms = {}
    tasks = {}

    for key, value in networks.items():
        web3 = Web3(Web3.HTTPProvider(value))
        network_stats[key] = web3.eth.get_block_number()

    for application in applications['Parameters']:
        alarm = False
        _network = str(application["Name"]).split("/")[3]

        delta = int(network_stats[_network]) - int(application["Value"])
        if delta > suggested_threshold():
            alarm = True
            alarms[_network] = alarm

        try:
            if alarms[_network]:
                pass
        except KeyError as e:
            alarms[_network] = alarm

        tasks[application["Name"]] = int(application["Value"])

    content["tasks"] = tasks
    content["alarms"] = alarms
    content["network_height"] = network_stats
    content["stats"] = retrieve_stats()

    return {
        'statusCode': 200,
        'body': json.dumps(content)
    }
