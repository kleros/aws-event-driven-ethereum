# Event Driven Ethereum using Lambdas and Parameter Store
This is a deployable SAM repository that deploys:
1. Lambda on a 15min schedule that checks for mutations on a smart contract
2. Notifies a SQS/SNS/S3 
It uses Parameter store to determine what needs checking and to store block height.
## Prereq
1. pip install aws-sam-cli
## Deployment
1. export AWS credentials
2. sam build --use-container
3. sam deploy --guided 

The intention of this tool was to abstract part of the event processing logic away from bots. 
## Production recommendation
Isolated accounts with unique RPC (Infura/Alchemy/Pokt.Network) endpoints for a low-cost approach.
Archive node endpoints should work well too.
If working with >50 watched contracts, consider running the lambda more often by changing the CloudWatch event trigger.
## Gotchas
1. At-least once message delivery, do your own *idempotency* if working e.g. with transactional operations.

## Required parameters:
1. `/ede/config/mainnet` = Ethereum RPC endpoint.
2. `/ede/config/gnosis` = Gnosis RPC endpoint.
3. Various VPC/Subnet  parameters, see `template.yaml`.

## Write ABI
I use a dynamodb to store the ABI of the contracts. The key in dynamo should match "ContractName" in SSM

## Watching a contract
`/ede/tasks/mainnet/<ContractName>/<Event>/<ContractAddress>`

Example:
`/ede/tasks/mainnet/ProofOfHumanity/AddSubmission/0xC5E9dDebb09Cd64DfaCab4011A0D5cEDaf7c9BDb`
This watches a ProofOfHumanity contract at 0xC5..
Your SSM can be tagged with SQS or SNS to receive notifications in form of the tx hash.


todo: implement smart contract version management
