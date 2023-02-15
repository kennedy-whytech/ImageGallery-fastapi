# A simple photo upload web via Fast-api with local S3 & Dynamodb

## setup local dyanmodb
```
docker run -d -p 8000:8000 --name local-dynamodb amazon/dynamodb-local
docker logs -f local-dynamodb
```
https://hub.docker.com/r/amazon/dynamodb-local

## setup local s3
```
docker run -p 9090:9090 -p 9191:9191 -e initialBuckets=test -e debug=true -t adobe/s3mock
```
https://github.com/adobe/S3Mock

## run the fast-api at port 8086
```
uvicorn main:app --port 8086 --reload 
```

## run it with docker
```
docker build -t gallary_fast_api .
docker run -e ENV_NAME=development gallary_fast_api
```
