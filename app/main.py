from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from jinja2 import Environment, FileSystemLoader
from io import BytesIO
from PIL import Image
import boto3
import uuid
import random
import string
from dotenv import load_dotenv
import os
import boto3
import botocore.session
import base64
load_dotenv()

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

ENV_NAME                = os.getenv("ENV_NAME", "development")
ORI_IMAGES_BUCKET       = os.getenv("ORI_IMAGES_BUCKET", 'oriimagesbucket7566')
RESIZED_IMAGES_BUCKET   = os.getenv("RESIZED_IMAGES_BUCKET", 'resizedimagesbucket7566')
DYANMODB_TABLE_NAME     = os.getenv("DYANMODB_TABLE_NAME", "image_meta")

print('This app is running in {} ENV'.format(ENV_NAME))
env = Environment(loader=FileSystemLoader('templates'))
print(ORI_IMAGES_BUCKET)
print(RESIZED_IMAGES_BUCKET)


if ENV_NAME == "development":
    region="us-east-1"
    dynamodb = boto3.resource('dynamodb', endpoint_url='http://dynamodb:8000', region_name=region) 
    s3 = boto3.resource('s3', endpoint_url='http://s3mock:9090', region_name=region)
    s3_client = boto3.client('s3', endpoint_url='http://s3mock:9090', region_name=region)

elif ENV_NAME == "production":
    region="us-east-1"
    dynamodb = boto3.resource('dynamodb', region_name=region)
    s3 = boto3.resource('s3', region_name=region)
    s3_client = boto3.client('s3', region_name=region)

# Dynamodb tables setup
try:
    # Try to get the table
    table = dynamodb.Table(DYANMODB_TABLE_NAME)
    table.load()
except dynamodb.meta.client.exceptions.ResourceNotFoundException:
    # Table does not exist, so create it
    table = dynamodb.create_table(
        TableName=DYANMODB_TABLE_NAME,
        KeySchema=[
            {
                'AttributeName': 'id',
                'KeyType': 'HASH'
            }
        ],
        AttributeDefinitions=[
            {
                'AttributeName': 'id',
                'AttributeType': 'S'
            }
        ],
        ProvisionedThroughput={
            'ReadCapacityUnits': 5,
            'WriteCapacityUnits': 5
        }
    )
    table.wait_until_exists()

table = dynamodb.Table(DYANMODB_TABLE_NAME)

# S3 bucket setup
bucket_list = [bucket['Name'] for bucket in s3_client.list_buckets()['Buckets']]

if ORI_IMAGES_BUCKET not in bucket_list:
    response = s3_client.create_bucket(
    Bucket=ORI_IMAGES_BUCKET
    )
    print(response)
if RESIZED_IMAGES_BUCKET not in bucket_list:
    response = s3_client.create_bucket(
    Bucket=RESIZED_IMAGES_BUCKET
    )
    print(response)
print("bucket_list: {}".format(bucket_list))

def returnDBRecords():
    response = table.scan()
    items = response['Items']
    template = env.get_template('index.html')
    for item in items:
        print(item['filename'])
        image_obj = s3_client.get_object(Bucket=RESIZED_IMAGES_BUCKET, Key=item['thumbnail_id'])['Body'].read()
        ori_url =s3_client.generate_presigned_url('get_object',
                                                    Params={'Bucket': ORI_IMAGES_BUCKET,
                                                            'Key': item['original_id']})
        item['img_b64'] = base64.b64encode(image_obj).decode('utf-8')
        item['ori_url'] = ori_url

    return HTMLResponse(template.render(items=items))

@app.get('/')
def index():
    return returnDBRecords()

def create_thumbnail(file):
    # create a thumbnail image from the original image file.
    with Image.open(file) as image:
        # Calculate the thumbnail size while preserving the aspect ratio
        max_size = (100, 100)
        image.thumbnail(max_size, resample=Image.LANCZOS)

        # Convert the image to JPEG format and return the binary data
        with BytesIO() as buffer:
            image.save(buffer, 'PNG')
            return buffer.getvalue()

@app.post('/uploadimage')
async def upload_image(file: UploadFile = File(...), title: str = Form(...), description: str = Form(...), tags: str = Form(...)):

    record_id = ''.join(random.choice(string.ascii_lowercase) for i in range(10))


    # Upload the original image to S3
    original_name = file.filename
    original_id   = record_id+original_name
    original_object = s3_client.put_object(
        Bucket=ORI_IMAGES_BUCKET,
        Key=original_id,
        Body=file.file
    )

    # Create a thumbnail of the image and upload it to S3
    thumbnail_name = 'thumbnail_' + original_name
    thumbnail_id   = record_id+thumbnail_name
    thumbnail_data = create_thumbnail(file.file)
    thumbnail_object = s3_client.put_object(
        Bucket=RESIZED_IMAGES_BUCKET,
        Key=thumbnail_id,
        Body=thumbnail_data
    )

    item = {
        'id': record_id,
        'filename': original_name,
        'original_id': original_id,
        'thumbnail': thumbnail_name,
        'thumbnail_id': thumbnail_id,
        'title': title,
        'description': description,
        'tags': tags
    }

    table.put_item(Item=item)
    return returnDBRecords()

