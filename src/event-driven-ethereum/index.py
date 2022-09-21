import os
import json
from tools import retrieve_tasks, update_block_height, retrieve_web3_endpoint
from botocore.config import Config
import boto3
from web3 import Web3
import logging


# AWS Resources
REGION = os.environ['AWS_REGION']
TABLE = os.environ.get('TABLE')

# network name e.g. gnosis, ethereum
NETWORK = os.environ.get('network')

boto_config = Config(
    region_name = REGION,
    signature_version = 'v4',
    retries = {
        'max_attempts': 10,
        'mode': 'standard'
    }
)

# Boto clients init
client = boto3.client('events', config=boto_config)
client_sns = boto3.client('sns', config=boto_config)
client_ssm = boto3.client('ssm', config=boto_config)
client_dydb = boto3.client('dynamodb', config=boto_config)
client_sqs = boto3.client('sqs', config=boto_config)


def retrieve_events(original_event, event_filter):
    for event in event_filter.get_all_entries():
        tx = event['transactionHash'].hex()
        logging.info(f"Found event: {tx}")

        if 'SQS' in original_event:
            client_sqs.send_message(
                QueueUrl=original_event['SQS'],
                MessageBody=tx,
            )
        if 'SNS' in original_event:
            client_sns.publish(
                TopicArn=original_event['SNS'],
                Message=tx,
                Subject=original_event['network']
            )
        if 'DynamoDB' in original_event:
            TABLE = client_dydb.Table(original_event['DynamoDB'])
            TABLE.update_item(Key={'tx': tx, 'network': original_event['network']})


def event_handler(event):
    task = event['task']
    try:
        retrieved_abi = str(client_dydb.get_item(
            TableName=TABLE,
            Key={'id': {'S': str(event['contract_name'])}})['Item']['abi']['S']
        )
    except BaseException as error:
        logging.error(f'Error retrieving ABI for {task}; has the ABI been added to the table?')
        logging.debug(error)

    # Retrieve RPC Endpoint from SSM
    endpoint = retrieve_web3_endpoint(client_ssm, NETWORK)
    contract = Web3.toChecksumAddress(event['address'])

    web3 = Web3(Web3.HTTPProvider(endpoint))
    contract = web3.eth.contract(address=contract, abi=retrieved_abi)
    latest = web3.eth.get_block_number()

    block_number = event['height']
    '''
    If this is the first time for a filter, start filtering 10 blocks from the latest block.
    To start filtering from a specific block run once or create the SSM parameter.
    '''
    if not block_number:
        block_number = int(int(latest)-int(10))

    ''' Because there is an eval here, do some sanity checks on the input vars to prevent arbitrary code execution.'''
    if not task.isalpha():
        logging.error(f'Stopping execution on {task}.')
        return

    event_filter = eval(str(f'contract.events.{task}.createFilter(fromBlock={block_number}, toBlock={latest})'))
    retrieve_events(event, event_filter)

    '''Updates the Block_height param in SSM; this way the software knows from where to retrieve from next.'''
    try:
        update_block_height(client_ssm, event, latest)
    except BaseException as error:
        logging.info(f"Couldn't update block height in SSM; verify IAM permissions.")
        logging.debug(error)


def lambda_entrypoint(event, context):
    '''1. Retrieve rules & for each of those rules scan for new events on a given Smart Contract and method.'''
    tasks = retrieve_tasks(client_ssm, NETWORK)
    for t in tasks.values():
        t = json.loads(t)  # Nested dict of tasks.
        try:
            event_handler(t)
        except Exception as e:
            logging.error(f'Failure on {t}')
            logging.error(e)
        finally:
            continue
