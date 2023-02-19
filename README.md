# ImageGallery-fastapi
## A simple image galary web via Fast-api with local S3 & Dynamodb. 
### Next, will provision necessary resoruces via AWS Cloudformation and deploy the docker in an EC2 instance connected with Dyanmo & S3

### 

### setup local dyanmodb. Files will be written to memory only. Table content can be reviewed via a local dynamodb-admin gui
```
docker run -d -p 8000:8000 --name local-dynamodb amazon/dynamodb-local
docker logs -f local-dynamodb
npm install -g dynamodb-admin
dynamodb-admin
```
https://hub.docker.com/r/amazon/dynamodb-local
https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/DynamoDBLocal.UsageNotes.html

### setup local s3
```
docker run -p 9090:9090 -p 9191:9191 -e initialBuckets=test -e debug=true -t adobe/s3mock
```
https://github.com/adobe/S3Mock

### run the fast-api at port 8086
```
uvicorn main:app --port 8006 --reload 
```

### configure the aws-cli credential in $HOME/.aws then run it with docker locally. Replace the env with your own config
```
docker build -t kennedydocker/gallery_fast_api:latest .
docker run --network host -e ENV_NAME=development -e ORI_IMAGES_BUCKET=oriimagesbucket7566 -e RESIZED_IMAGES_BUCKET=resizedimagesbucket7566 -e DYANMODB_TABLE_NAME=image_meta --mount type=bind,source=$HOME/.aws,target=/root/.aws kennedydocker/gallery_fast_api:latest
```

### The cloudformation stack will be in another repo


### public to dockerhub
```
docker build --no-cache -t kennedydocker/gallery_fast_api:latest .
docker push kennedydocker/gallery_fast_api:latest
```

### prerequisite- 1. create s3 buckets 2. create dynamodb table
### on EC2. --network host may not work in a mac
```
docker run -e ENV_NAME=production -e ORI_IMAGES_BUCKET=oriimagesbucket7566 -e RESIZED_IMAGES_BUCKET=resizedimagesbucket7566 -e DYANMODB_TABLE_NAME=image_meta -p 8006:8006 kennedydocker/gallery_fast_api:latest
```
