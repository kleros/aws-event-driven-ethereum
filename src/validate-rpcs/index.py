import os
import boto3
from web3 import Web3

REGION = os.environ.get("REGION")
ssm_client = boto3.client("ssm", REGION)


def retrieve_configs(network):
    default = ssm_client.get_parameter(Name=f"/ede/config/{network}")['Parameter']['Value']
    active = ssm_client.get_parameter(Name=f"/ede/active/{network}")['Parameter']['Value']
    fallback = ssm_client.get_parameter(Name=f"/ede/fallback/{network}")['Parameter']['Value']
    return default, active, fallback


def check_rpc(endpoint):
    web3 = Web3(Web3.HTTPProvider(endpoint))
    connected = web3.isConnected()
    if not connected:
        return connected,  None
    return connected, web3.eth.get_block("latest" )


MAX_DIFF = 10


def challenge_rpcs(defendant, challenger):
    r = False
    if defendant > challenger:
        diff = defendant - challenger
        if diff < MAX_DIFF:
            r = True
    if challenger > defendant:
        diff = challenger - defendant
        if diff > MAX_DIFF:
            r = True
    return r


def update_config(rpc, network):
    return ssm_client.put_parameter(Name=f'/ede/active/{network}', Value=rpc, Type='String', Overwrite=True)


def get_networks():
    networks = ("mainnet", "gnosis")
    return networks


def bot_logic():
    for network in get_networks():
        default, active, fallback = retrieve_configs(network)
        fallback_status, fallback_height = check_rpc(fallback)
        if fallback is active:
            default_status, default_height = check_rpc(default)
            if default_status:
                winner = challenge_rpcs(fallback_height, default_height)
                if winner:
                    update_config(default)
        return

        active_status, active_height = check_rpc(active)
        if active_status:
            winner = challenge_rpcs(active_height, fallback_height)
        if not active_status or winner is True:
            update_config(fallback)

