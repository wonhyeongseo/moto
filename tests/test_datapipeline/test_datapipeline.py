from __future__ import unicode_literals

import boto.datapipeline
import sure  # noqa

from moto import mock_datapipeline


def get_value_from_fields(key, fields):
    for field in fields:
        if field['key'] == key:
            return field['stringValue']


@mock_datapipeline
def test_create_pipeline():
    conn = boto.datapipeline.connect_to_region("us-west-2")

    res = conn.create_pipeline("mypipeline", "some-unique-id")

    pipeline_id = res["pipelineId"]
    pipeline_descriptions = conn.describe_pipelines([pipeline_id])["PipelineDescriptionList"]
    pipeline_descriptions.should.have.length_of(1)

    pipeline_description = pipeline_descriptions[0]
    pipeline_description['Name'].should.equal("mypipeline")
    pipeline_description["PipelineId"].should.equal(pipeline_id)
    fields = pipeline_description['Fields']

    get_value_from_fields('@pipelineState', fields).should.equal("PENDING")
    get_value_from_fields('uniqueId', fields).should.equal("some-unique-id")


PIPELINE_OBJECTS = [
    {
        "id": "Default",
        "name": "Default",
        "fields": [{
            "key": "workerGroup",
            "stringValue": "workerGroup"
        }]
    },
    {
        "id": "Schedule",
        "name": "Schedule",
        "fields": [{
            "key": "startDateTime",
            "stringValue": "2012-12-12T00:00:00"
        }, {
            "key": "type",
            "stringValue": "Schedule"
        }, {
            "key": "period",
            "stringValue": "1 hour"
        }, {
            "key": "endDateTime",
            "stringValue": "2012-12-21T18:00:00"
        }]
    },
    {
        "id": "SayHello",
        "name": "SayHello",
        "fields": [{
            "key": "type",
            "stringValue": "ShellCommandActivity"
        }, {
            "key": "command",
            "stringValue": "echo hello"
        }, {
            "key": "parent",
            "refValue": "Default"
        }, {
            "key": "schedule",
            "refValue": "Schedule"
        }]
    }
]


@mock_datapipeline
def test_creating_pipeline_definition():
    conn = boto.datapipeline.connect_to_region("us-west-2")
    res = conn.create_pipeline("mypipeline", "some-unique-id")
    pipeline_id = res["pipelineId"]

    conn.put_pipeline_definition(PIPELINE_OBJECTS, pipeline_id)

    pipeline_definition = conn.get_pipeline_definition(pipeline_id)
    pipeline_definition['pipelineObjects'].should.have.length_of(3)
    default_object = pipeline_definition['pipelineObjects'][0]
    default_object['Name'].should.equal("Default")
    default_object['Id'].should.equal("Default")
    default_object['Fields'].should.equal([{
        "key": "workerGroup",
        "stringValue": "workerGroup"
    }])


@mock_datapipeline
def test_describing_pipeline_objects():
    conn = boto.datapipeline.connect_to_region("us-west-2")
    res = conn.create_pipeline("mypipeline", "some-unique-id")
    pipeline_id = res["pipelineId"]

    conn.put_pipeline_definition(PIPELINE_OBJECTS, pipeline_id)

    objects = conn.describe_objects(["Schedule", "Default"], pipeline_id)['PipelineObjects']

    objects.should.have.length_of(2)
    default_object = [x for x in objects if x['Id'] == 'Default'][0]
    default_object['Name'].should.equal("Default")
    default_object['Fields'].should.equal([{
        "key": "workerGroup",
        "stringValue": "workerGroup"
    }])


@mock_datapipeline
def test_activate_pipeline():
    conn = boto.datapipeline.connect_to_region("us-west-2")

    res = conn.create_pipeline("mypipeline", "some-unique-id")

    pipeline_id = res["pipelineId"]
    conn.activate_pipeline(pipeline_id)

    pipeline_descriptions = conn.describe_pipelines([pipeline_id])["PipelineDescriptionList"]
    pipeline_descriptions.should.have.length_of(1)
    pipeline_description = pipeline_descriptions[0]
    fields = pipeline_description['Fields']

    get_value_from_fields('@pipelineState', fields).should.equal("SCHEDULED")


@mock_datapipeline
def test_listing_pipelines():
    conn = boto.datapipeline.connect_to_region("us-west-2")
    res1 = conn.create_pipeline("mypipeline1", "some-unique-id1")
    res2 = conn.create_pipeline("mypipeline2", "some-unique-id2")
    pipeline_id1 = res1["pipelineId"]
    pipeline_id2 = res2["pipelineId"]

    response = conn.list_pipelines()

    response["HasMoreResults"].should.be(False)
    response["Marker"].should.be.none
    response["PipelineIdList"].should.equal([
        {
            "Id": res1["pipelineId"],
            "Name": "mypipeline1",
        },
        {
            "Id": res2["pipelineId"],
            "Name": "mypipeline2"
        }
    ])
