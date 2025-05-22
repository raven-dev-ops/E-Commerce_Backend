#!/bin/bash

APP_NAME="twiinz-beard-backend"
HEROKU_IMAGE_TAG="registry.heroku.com/$APP_NAME/web"

echo "Logging into Heroku container registry..."
heroku container:login

echo "Setting Heroku stack to container..."
heroku stack:set container -a $APP_NAME

echo "Building new Docker image (linux/amd64) directly with Heroku tag..."
docker build --platform=linux/amd64 --no-cache -t $HEROKU_IMAGE_TAG .

echo "Pushing Docker image..."
docker push $HEROKU_IMAGE_TAG # This will push registry.heroku.com/twiinz-beard-website/web:latest

echo "Releasing Docker container..."
heroku container:release web

echo "Tailing logs..."
heroku logs --tail -a $APP_NAME