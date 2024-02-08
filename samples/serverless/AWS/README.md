![CrowdStrike Falcon](https://raw.githubusercontent.com/CrowdStrike/falconpy/main/docs/asset/cs-logo.png)

[![CrowdStrike Subreddit](https://img.shields.io/badge/-r%2Fcrowdstrike-white?logo=reddit&labelColor=gray&link=https%3A%2F%2Freddit.com%2Fr%2Fcrowdstrike)](https://reddit.com/r/crowdstrike)

# AWS Lambda automation examples
The examples in this folder focus on leveraging CrowdStrike APIs within AWS Lambda to automate maintenance, reporting and response operations.

- [Authentication](#authentication)
- [Examples](#examples)
- [Lambda layers](#aws-lambda-layers)

## Authentication
Credentials for these examples are securely retrieved leveraging [AWS Systems Manager Parameter Store](https://docs.aws.amazon.com/systems-manager/latest/userguide/systems-manager-parameter-store.html).

Lambda function permissions to newly created AWS Systems Manager Parameter Store secrets will need to be granted before credentials can be successfully retrieved. 

An example of a policy that provides these permissions:

```json
{
    "Effect": "Allow",
    "Action": "secretsmanager:GetSecretValue",
    "Resource": "arn:aws:secretsmanager:region:account-id:secret:secret-name"
}
```

> [!TIP]
> Update the value of the `Resource` key above to match your environment.

This policy should be attached to the execution role of the lambda function and should have the following trust relationship.

```json
{
    "Effect": "Allow",
    "Principal": {
        "Service": "lambda.amazonaws.com"
    },
    "Action": "sts:AssumeRole"
}
```

## Lambda function examples
> [!NOTE]
> The following AWS Lambda automation examples require the `crowdstrike-falconpy` library to be attached as a layer. For more details, review the contents of the [AWS Lambda layers](#aws-lambda-layers) section below.

- [EDR API](#edr-api)
- [Artifactory Installer Update](#artifactory-installer-update)
- [FalconBot (EDR)](#falconbot-edr)
- [Intel Downloads](#intel-downloads)
- [Pick Next Sensor Version](#pick-next-sensor-version)
- [Sensor Version Change](#sensor-version-change)
- [Update Supported Kernels List](#update-supported-kernels-list)

### EDR API
The EDR API is a single AWS Lambda function that leverages AWS API Gateway to operate as a wrapper for several CrowdStrike API operations. This solution leverages DynamoDB on the backend to store information regarding latest kernels, sensor date changes, and sensor versions.

There is also a health check endpoint that allows a team to call the API to check the health of an individual host programmatically. In order to use the Health Check you will need to provide CrowdStrike API client credentials with host read permissions.  

#### Function requirements
In order for this function to execute properly, it will need access to CrowdStrike API keys with the following scopes:

| Service Collection | Scope |
| :---- | :---- |
| Hosts | __READ__ |
| Sensor Download | __READ__ |
| Sensor Update Policy | __READ__ |

This function requires an attached layer with the following packages included:

- `crowdstrike-falconpy`

This function leverages a DynamoDB that will require the following tables:

- Container_Paths  
- Latest_Kernel  
- Sensor_Versions  
- Proposed_Sensor Versions  
- Change_Dates (Dates will be manually added in the format of `yyyy-mm-dd`. Example: _2023-01-01_)

> [!NOTE]
> The lambda function will also need permissions to the related DynamoDB.

#### Example source code
The source code for this example can be found [here](EDR_API).

### Artifactory Installer Update
This lambda automation is designed to pull down the latest Sensor Installers from the Falcon API and upload them to an Artifactory server.

#### Function requirements
In order for this function to execute properly, it will need access to CrowdStrike API keys with the following scopes:

| Service Collection | Scope |
| :---- | :---- |
| Sensor Download | __READ__ |
| Sensor Update Policy | __READ__ |

This function requires an attached layer with the following packages included:

- `crowdstrike-falconpy`

The lambda timeout will need to be set to `15 minutes`, memory to `1024MB` and the ephemeral storage to `2048MB`.

> [!NOTE]
> Please review the contents of this script carefully as there are several places where you will need to update values to match your environment.

#### Example source code
The source code for this example can be found [here](ArtifactoryInstallerUpdate.py).

### FalconBot (EDR)
Provide updates from CrowdStrike EDR directly to Slack.

#### Function requirements
In order for this function to execute properly, it will need access to CrowdStrike API keys with the following scopes:

| Service Collection | Scope |
| :---- | :---- |
| Sensor Download | __READ__ |
| Sensor Update Policy | __READ__ |

This function requires an attached layer with the following packages included:

- `crowdstrike-falconpy`
- `tabulate`

#### Example source code
The source code for this example can be found [here](FalconBot-EDR_End.py) and [here](FalconBot-SlackEnd).

### Intel Downloads
This automation is used to download the daily intel report from the Falcon Console and send it to a distribution list via email and Slack.

#### Function requirements
In order for this function to execute properly, it will need access to CrowdStrike API keys with the following scopes:

| Service Collection | Scope |
| :---- | :---- |
| Reports (Falcon Intelligence) | __READ__ |

This function requires an attached layer with the following packages included:

- `crowdstrike-falconpy`

#### Example source code
The source code for this example can be found [here](IntelDownloads.py).

### Pick Next Sensor Version
This automation will pick the next sensor version for you based off the current CrowdStrike N-1 version and your current development version.

#### Function requirements
In order for this function to execute properly, it will need access to CrowdStrike API keys with the following scopes:

| Service Collection | Scope |
| :---- | :---- |
| Sensor Download | __READ__ |
| Sensor Update Policy | __READ__ |

This function requires an attached layer with the following packages included:

- `crowdstrike-falconpy`

#### Example source code
The source code for this example can be found [here](PickNextSensorVersion.py).

### Sensor Version Change
This Lambda function will update sensor versions in accordance with the change schedule. It will also update the sensor versions in the [EDR API](#edr-api) Database and the Wiki page.

#### Function requirements
In order for this function to execute properly, it will need access to CrowdStrike API keys with the following scopes:

| Service Collection | Scope |
| :---- | :---- |
| Sensor Update Policy | __READ__, __WRITE__ |

This function requires an attached layer with the following packages included:

- `crowdstrike-falconpy`

#### Example source code
The source code for this example can be found [here](Sensor_version_change.py).

### Update Supported Kernels List
This Lambda function will query the CrowdStrike API for the list of supported kernels and output them to an HTML file in an S3 bucket.

#### Function requirements
In order for this function to execute properly, it will need access to CrowdStrike API keys with the following scopes:

| Service Collection | Scope |
| :---- | :---- |
| Sensor Update Policy | __READ__ |

This function requires an attached layer with the following packages included:

- `crowdstrike-falconpy`
- `natsort`

#### Example source code
The source code for this example can be found [here](UpdateSupportedKernelsList_Sorted.py).

## AWS Lambda layers
A lambda layer is a `zip` formatted archive that contains supplementary code or data for a function. Layers typically contain library dependencies, custom runtimes, or configuration files. More information regarding AWS Lambda layers can be found [here](https://docs.aws.amazon.com/lambda/latest/dg/chapter-layers.html).

All of the examples within this folder will require the `crowdstrike-falconpy` package to be included in an attached lambda layer. For examples that contain multiple dependencies, these can be attached via a single layer, or multiple as per the needs of environment.

For an example of generating a layer containing FalconPy locally please check the script maintained in this repository's `util` folder [here](https://github.com/CrowdStrike/falconpy/blob/main/util/create-lambda-layer.sh).

### Example layer generation including multiple Python packages
This example leverages the example linked above to create a lambda layer that includes the `crowdstrike-falconpy` and `tabulate` packages.

```shell
#!/bin/bash
# Create a requirements file containing our package list
cat - << EOF > lambda-requirements.txt
crowdstrike-falconpy
tabulate
EOF
# Remove any old copies of the layer
rm falconpy-layer.zip >/dev/null 2>&1
# Run the image and install the requirements
docker run --rm --entrypoint '' -v $(pwd):/foo -w /foo public.ecr.aws/lambda/python:3.8 \
pip install -r lambda-requirements.txt -t python
# Create the layer archive
zip -r falconpy-layer.zip python
# Clean up
rm -fR python
rm lambda-requirements.txt
```

### Standardized layer downloads
Don't want to generate your own layer? Details regarding downloading a standard layer containing the most recent version of FalconPy can be found in [this discussion](https://github.com/CrowdStrike/falconpy/discussions/496). 

### Attaching layers to a lambda function
For information regarding how to attach layers to AWS Lambda functions, please review the contents of [this](https://docs.aws.amazon.com/lambda/latest/dg/adding-layers.html) page.
