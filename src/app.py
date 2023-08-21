import gpxpy
import gpxpy.gpx
import boto3
from datetime import datetime
from dateutil.parser import parse

def lambda_handler(event, context):
    # device_01から05までのデータに対してgpxファイルを生成
    for i in range(1, 6):
        device_id = 'device_0' + str(i)
        data = get_data_from_dynamodb(device_id)
        gpx = create_gpx(data)
        upload_gpx_to_s3(gpx, device_id + '.gpx')

# DynamoDBから特定のdevice_idのデータを取得
def get_data_from_dynamodb(device_id):
    result = []
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('dynamo-gpx')

    response = table.query(
        KeyConditionExpression=boto3.dynamodb.conditions.Key('device_id').eq(device_id)
    )
    items = response.get('Items', [])

    while 'LastEvaluatedKey' in response:
        response = table.query(
            KeyConditionExpression=boto3.dynamodb.conditions.Key('device_id').eq(device_id),
            ExclusiveStartKey=response['LastEvaluatedKey']
        )
        items.extend(response.get('Items', []))

    return items

# GPXファイルを生成
def create_gpx(data):
    gpx = gpxpy.gpx.GPX()

    # Create first track in our GPX:
    gpx_track = gpxpy.gpx.GPXTrack()
    gpx.tracks.append(gpx_track)

    # Create first segment in our GPX track:
    gpx_segment = gpxpy.gpx.GPXTrackSegment()
    gpx_track.segments.append(gpx_segment)

    # Create points:
    for d in data:
        gpx_segment.points.append(gpxpy.gpx.GPXTrackPoint(d['lat'], d['lng'], time=parse(d['timestamp'])))

    return gpx

# S3にgpxファイルをアップロード
def upload_gpx_to_s3(gpx, key):
    s3 = boto3.resource('s3')
    s3.Bucket('dynamo-gpx').put_object(Key=key, Body=gpx.to_xml())