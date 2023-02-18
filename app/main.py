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

app = FastAPI()

ENV_NAME                = os.getenv("ENV_NAME", "development")
ORI_IMAGES_BUCKET       = os.getenv("ORI_IMAGES_BUCKET", 'oribucket'+''.join(random.choice(string.ascii_lowercase) for i in range(5)))
RESIZED_IMAGES_BUCKET   = os.getenv("RESIZED_IMAGES_BUCKET", 'resizedbucket'+''.join(random.choice(string.ascii_lowercase) for i in range(5)))
DYANMODB_TABLE_NAME     = os.getenv("DYANMODB_TABLE_NAME", "image_meta")

print('This app is running in %s ENV'.format(ENV_NAME))
env = Environment(loader=FileSystemLoader('templates'))


print(ori_bucket_name)
print(resize_bucket_name)

def init_bucket(s3_client):
    response = s3_client.create_bucket(
        Bucket=ori_bucket_name
    )
    print(response)

    response = s3_client.create_bucket(
        Bucket=resize_bucket_name
    )
    print(response)

if ENV_NAME == "development":
    dynamodb = boto3.resource('dynamodb', endpoint_url='http://localhost:8000')
    table = dynamodb.Table(DYANMODB_TABLE_NAME)
    s3 = boto3.resource('s3', endpoint_url='http://localhost:9090')
    s3_client = boto3.client('s3', endpoint_url='http://localhost:9090')

    #init_bucket(s3_client, ori_bucket_name, resize_bucket_name)
elif ENV_NAME == "production":
    region=boto3.session.Session().region_name
    dynamodb = boto3.resource('dynamodb', region_name=region)
    table = dynamodb.Table(DYANMODB_TABLE_NAME)
    s3 = boto3.resource('s3', region_name=region)
    s3_client = boto3.client('s3', region_name=region)

def returnDBRecords():
    response = table.scan()
    items = response['Items']
    template = env.get_template('index.html')
    # Get temp accessible object url
    for item in items:
        # there's still some issue with the local object_url
        object_url = s3_client.generate_presigned_url(
            ClientMethod='get_object',
            Params={
                'Bucket': resize_bucket_name,
                'Key': item['filename']
            },
            ExpiresIn=3600
            )
        item['object_url'] = object_url
    print(item)

    return HTMLResponse(template.render(items=items))


@app.get('/')
def index():
    return returnDBRecords()

def create_thumbnail(file):
    """Create a thumbnail image from the original image file."""
    with Image.open(file) as image:
        # Calculate the thumbnail size while preserving the aspect ratio
        max_size = (100, 100)
        image.thumbnail(max_size, resample=Image.LANCZOS)

        # Convert the image to JPEG format and return the binary data
        with BytesIO() as buffer:
            image.convert('RGB').save(buffer, 'JPEG')
            return buffer.getvalue()

@app.post('/uploadimage')
async def upload_image(file: UploadFile = File(...), title: str = Form(...), description: str = Form(...), tags: str = Form(...)):

    # Upload the original image to S3
    original_name = file.filename
    original_object = s3_client.put_object(
        Bucket=ori_bucket_name,
        Key=original_name,
        Body=file.file
    )

    # Create a thumbnail of the image and upload it to S3
    thumbnail_name = 'thumbnail_' + original_name
    thumbnail_data = create_thumbnail(file.file)
    thumbnail_object = s3_client.put_object(
        Bucket=resize_bucket_name,
        Key=thumbnail_name,
        Body=thumbnail_data
    )

    item = {
        'id': ''.join(random.choice(string.ascii_lowercase) for i in range(10)),
        'filename': original_name,
        'thumbnail': thumbnail_name,
        'title': title,
        'description': description,
        'tags': tags
    }

    table.put_item(Item=item)
    return returnDBRecords()

