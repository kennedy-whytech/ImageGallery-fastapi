# gallery-fast-api
## A simple image galary web via Fast-api with local S3 & Dynamodb. 
### Next, will provision necessary resoruces via AWS Cloudformation and deploy the docker in an EC2 instance connected with Dyanmo & S3

### setup local dyanmodb
```
docker run -d -p 8000:8000 --name local-dynamodb amazon/dynamodb-local
docker logs -f local-dynamodb
```
https://hub.docker.com/r/amazon/dynamodb-local

### setup local s3
```
docker run -p 9090:9090 -p 9191:9191 -e initialBuckets=test -e debug=true -t adobe/s3mock
```
https://github.com/adobe/S3Mock

### run the fast-api at port 8086
```
uvicorn main:app --port 8086 --reload 
```

### configure the aws-cli credential in $HOME/.aws then run it with docker locally. Replace the env with your own config
```
docker build -t gallary_fast_api .
docker run -e ENV_NAME=development -p 8086:8086 gallary_fast_api
docker run -e ENV_NAME=development -e ORI_IMAGES_BUCKET=oriimagesbucket7566 -e RESIZED_IMAGES_BUCKET=resizedimagesbucket7566 -e DYANMODB_TABLE_NAME=image_meta --network host --mount type=bind,source=$HOME/.aws,target=/root/.aws gallary_fast_api
```

### The cloudformation stack will be in another repo

### on EC2
```
docker run -e ENV_NAME=production -e ORI_IMAGES_BUCKET=oriimagesbucket7566 -e RESIZED_IMAGES_BUCKET=resizedimagesbucket7566 -e DYANMODB_TABLE_NAME=image_meta -p 8086:8086 gallary_fast_api
```
