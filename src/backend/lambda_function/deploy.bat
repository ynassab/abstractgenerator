set DIRECTORY=%cd%
set LAYER_IMAGE=lambda-layer
set LAYER_CONTAINER=lambda-layer-container

C:\"Program Files"\Docker\Docker\"Docker Desktop.exe"
docker build --platform linux/amd64 -t %LAYER_IMAGE% %DIRECTORY% && python push_image_to_aws.py
docker rmi --force %LAYER_IMAGE%
