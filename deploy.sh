#!/bin/bash

APP_NAME="twiinz-beard-backend"

echo "Logging into Heroku container registry..."
heroku container:login

echo "Building new Docker image and tagging for Heroku registry..."
docker build --no-cache -t registry.heroku.com/$APP_NAME/web .

echo "Pushing Docker image to Heroku..."
docker push registry.heroku.com/$APP_NAME/web

echo "Releasing Docker container on Heroku..."
heroku container:release web -a $APP_NAME

echo "Restarting dynos to force new image deployment..."
heroku ps:restart -a $APP_NAME

echo "Checking process status..."
heroku ps -a $APP_NAME

echo "Tailing logs..."
heroku logs --tail -a $APP_NAME
