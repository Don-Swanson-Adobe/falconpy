"""Internal API endpoint constant library.

 _______                        __ _______ __        __ __
|   _   .----.-----.--.--.--.--|  |   _   |  |_.----|__|  |--.-----.
|.  1___|   _|  _  |  |  |  |  _  |   1___|   _|   _|  |    <|  -__|
|.  |___|__| |_____|________|_____|____   |____|__| |__|__|__|_____|
|:  1   |                         |:  1   |
|::.. . |   CROWDSTRIKE FALCON    |::.. . |    FalconPy
`-------'                         `-------'

OAuth2 API - Customer SDK

This is free and unencumbered software released into the public domain.

Anyone is free to copy, modify, publish, use, compile, sell, or
distribute this software, either in source code form or as a compiled
binary, for any purpose, commercial or non-commercial, and by any
means.

In jurisdictions that recognize copyright laws, the author or authors
of this software dedicate any and all copyright interest in the
software to the public domain. We make this dedication for the benefit
of the public at large and to the detriment of our heirs and
successors. We intend this dedication to be an overt act of
relinquishment in perpetuity of all present and future rights to this
software under copyright law.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
IN NO EVENT SHALL THE AUTHORS BE LIABLE FOR ANY CLAIM, DAMAGES OR
OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
OTHER DEALINGS IN THE SOFTWARE.

For more information, please refer to <https://unlicense.org>
"""

_falcon_container_endpoints = [
  [
    "GetCredentials",
    "GET",
    "/container-security/entities/image-registry-credentials/v1",
    "Gets the registry credentials",
    "falcon_container",
    []
  ],
  [
    "ReadImageVulnerabilities",
    "POST",
    "/image-assessment/combined/vulnerability-lookups/v1",
    "Retrieve known vulnerabilities for the provided image",
    "falcon_container_cli",
    [
      {
        "name": "body",
        "in": "body",
        "required": True
      }
    ]
  ],
  [
    "GetImageAssessmentReport",
    "GET",
    "/reports",
    "Retrieves the Assessment report for the Image ID provided.",
    "falcon_container",
    [
      {
        "type": "string",
        "description": "The hash digest for the image.",
        "name": "digest",
        "in": "query",
        "required": False
      },
      {
        "type": "string",
        "description": "The image ID.",
        "name": "image_id",
        "in": "query",
        "required": False
      },
      {
        "type": "string",
        "description": "The repository the image resides within.",
        "name": "repository",
        "in": "query",
        "required": False
      },
      {
        "type": "string",
        "description": "The image tag.",
        "name": "tag",
        "in": "query",
        "required": False
      }
    ]
  ],
  [
    "DeleteImageDetails",
    "DELETE",
    "/images/{}",
    "Delete Images by ids.",
    "falcon_container",
    [
      {
        "type": "string",
        "description": "The ID of the image to be deleted.",
        "name": "image_id",
        "in": "path",
        "required": True
      }
    ]
  ],
  [
    "ImageMatchesPolicy",
    "GET",
    "/policy-checks",
    "After an image scan, use this operation to see if any images match a policy. If deny is true,"
    " the policy suggestion is that you do not deploy the image in your environment.",
    "falcon_container",
    [
      {
        "type": "string",
        "description": "The repository the image resides within.",
        "name": "repository",
        "in": "query",
        "required": True
      },
      {
        "type": "string",
        "description": "The image tag.",
        "name": "tag",
        "in": "query",
        "required": True
      }
    ]
  ],
  [
    "ReadRegistryEntities",
    "GET",
    "/container-security/queries/registries/v1",
    "Retrieve registry entities identified by the customer ID.",
    "falcon_container_image",
    [
      {
        "type": "string",
        "description": "Starting index of result set from which to return IDs.",
        "name": "offset",
        "in": "query"
      },
      {
        "type": "integer",
        "description": "Number of IDs to return.",
        "name": "limit",
        "in": "query"
      },
      {
        "type": "string",
        "description": "Order by fields.",
        "name": "sort",
        "in": "query"
      }
    ]
  ],
  [
    "CreateRegistryEntities",
    "POST",
    "/container-security/entities/registries/v1",
    "Create a registry entity using the provided details.",
    "falcon_container_image",
    [
      {
        "name": "body",
        "in": "body",
        "required": True
      }
    ]
  ],
  [
    "DeleteRegistryEntities",
    "DELETE",
    "/container-security/entities/registries/v1",
    "Delete the registry entity identified by the entity UUID.",
    "falcon_container_image",
    [
      {
        "type": "string",
        "description": "Registry entity UUID.",
        "name": "ids",
        "in": "query",
        "required": True
      }
    ]
  ],
  [
    "UpdateRegistryEntities",
    "PATCH",
    "/container-security/entities/registries/v1",
    "Update the registry entity, as identified by the entity UUID, using the provided details.",
    "falcon_container_image",
    [
      {
        "type": "string",
        "description": "Registry entity UUID.",
        "name": "id",
        "in": "query",
        "required": True
      },
      {
        "name": "body",
        "in": "body",
        "required": True
      }
    ]
  ],
  [
    "ReadRegistryEntitiesByUUID",
    "GET",
    "/container-security/entities/registries/v1",
    "Retrieve the registry entity identified by the entity UUID.",
    "falcon_container_image",
    [
      {
        "type": "string",
        "description": "Registry entity UUID.",
        "name": "ids",
        "in": "query",
        "required": True
      }
    ]
  ],
  [
    "GetVulnerableContainerInfo",
    "GET",
    "/container-security/aggregates/containers/counts-by-vulnerable/v1",
    "Retrieve containers counts for the most vulnerable containers",
    "network_events",
    [
      {
        "type": "string",
        "description": "Filter images using a query in Falcon Query Language (FQL). Supported filters:  time_since",
        "name": "filter",
        "in": "query"
      }
    ]
  ],
  [
    "GetPodsWithMostOpenPorts",
    "GET",
    "/container-security/aggregates/pods/counts-by-open-port/v1",
    "Retrieve pods with the most open ports",
    "network_events",
    [
      {
        "type": "string",
        "description": "Filter images using a query in Falcon Query Language (FQL). Supported filters:  time_since",
        "name": "filter",
        "in": "query"
      }
    ]
  ],
  [
    "GetPortInfo",
    "GET",
    "/container-security/aggregates/ports/counts-by-open-state/v1",
    "Retrieve ports based on the given filter criteria",
    "network_events",
    [
      {
        "type": "string",
        "description": "Filter images using a query in Falcon Query Language (FQL). Supported filters:  time_since,type",
        "name": "filter",
        "in": "query"
      }
    ]
  ]
]
