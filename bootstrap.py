import boto3
import yaml
import os

REGION = os.environ.get("AWS_REGION")
ssm_client = boto3.client("ssm", REGION)

def ssm_write(path, value):
    return

def write_network_to_ssm(network, rpc):
    return

def write_subnets(subnets):
    i = 0
    for subnet in subnets:
        if i > 2:
            return
        az = ("a", "b", 'c')
        ssm_write(subnet, f"/subnet/{az[i]}")
        i += 1

with open("params.yaml", "r") as stream:
    try:
        d = dict(yaml.safe_load(stream))
    except yaml.YAMLError as exc:
        print(exc)

print(d)

for network  in d['networks']:
    rpc_endpoint = d['networks'][network]["rpc"]
    ssm_write(f"/ede/config/{network}", rpc_endpoint)
    ssm_write(f"/ede/active/{network}", rpc_endpoint)
    try:
        fallback_rpc = d['networks'][network]['fallback']
        ssm_write(f"/ede/fallback/{network}", fallback_rpc)
    except:
        continue

if d['vpc']['enabled']:
    vpc_id = d['vpc']['vpc_id']
    subnets = str(d['vpc']['subnets'])
    subnets = list(subnets.split(","))
    write_subnets(subnets)

ssm_write("prefix", d['org']['prefix'])
ssm_write("environment", d['org']['environment'])
ssm_write("vpc", d['vpc']['vpc_id'])