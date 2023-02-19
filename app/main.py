from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import HTMLResponse
from jinja2 import Environment, FileSystemLoader
from io import BytesIO
from PIL import Image
import boto3
import uuid
import random
import string
from dotenv import load_dotenv
import os
load_dotenv()
import boto3
import botocore.session
import base64


app = FastAPI()

ENV_NAME                = os.getenv("ENV_NAME", "development")
ORI_IMAGES_BUCKET       = os.getenv("ORI_IMAGES_BUCKET", 'oriimagesbucket7566')
RESIZED_IMAGES_BUCKET   = os.getenv("RESIZED_IMAGES_BUCKET", 'resizedimagesbucket7566')
DYANMODB_TABLE_NAME     = os.getenv("DYANMODB_TABLE_NAME", "image_meta")

print('This app is running in %s ENV'.format(ENV_NAME))
env = Environment(loader=FileSystemLoader('templates'))
print(ORI_IMAGES_BUCKET)
print(RESIZED_IMAGES_BUCKET)


if ENV_NAME == "development":
    region="us-east-1"
    dynamodb = boto3.resource('dynamodb', endpoint_url='http://localhost:8000', region_name=region)
    table = dynamodb.Table(DYANMODB_TABLE_NAME)
    s3 = boto3.resource('s3', endpoint_url='http://localhost:9090', region_name=region)
    s3_client = boto3.client('s3', endpoint_url='http://localhost:9090', region_name=region)

elif ENV_NAME == "production":
    region="us-east-1"
    dynamodb = boto3.resource('dynamodb', region_name=region)
    table = dynamodb.Table(DYANMODB_TABLE_NAME)
    s3 = boto3.resource('s3', region_name=region)
    s3_client = boto3.client('s3', region_name=region)


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
        item['img_b64'] = base64.b64encode(image_obj).decode('utf-8')
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
    original_id   = original_name+record_id
    original_object = s3_client.put_object(
        Bucket=ORI_IMAGES_BUCKET,
        Key=original_name,
        Body=file.file
    )

    # Create a thumbnail of the image and upload it to S3
    thumbnail_name = 'thumbnail_' + original_name
    thumbnail_id   = thumbnail_name+record_id
    thumbnail_data = create_thumbnail(file.file)
    thumbnail_object = s3_client.put_object(
        Bucket=RESIZED_IMAGES_BUCKET,
        Key=thumbnail_id,
        Body=thumbnail_data
    )

    item = {
        'id': record_id,
        'filename': original_name,
        'thumbnail': thumbnail_name,
        'thumbnail_id': thumbnail_id,
        'title': title,
        'description': description,
        'tags': tags
    }

    table.put_item(Item=item)
    return returnDBRecords()
