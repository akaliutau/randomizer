# About
A docker image with python application to study Kubernetes cluster

# Installation


```shell
python3 -m venv venv
source ./venv/bin/activate
pip install -r requirements.txt
```

# Running

To start local server
```shell
export PORT=8080
python3 app.py
```

(default port is 80 and is usually taken byh other processes)

# Building image

Test and dev built:

```shell
sudo docker  build -t randomizer:1.0 .
sudo docker run randomizer:1.0
```
Note, docker runs images in isolation mode by default and hence you cannot connect to localhost:8080. Use mapping instead:

```shell
docker run -d -p 8080:8080 randomizer:1.0
docker kill <container_id>
```

Production build:

```shell
docker buildx 
docker push
```

# API
| endpoint            | action                            |   
|---------------------|-----------------------------------|
 | /                   | returns random number             |
| /memory-loader?mb=3 | allocates memory buffer in 3 MB   |
| /toggle-live        | toggles liveness probe            |
| /toggle-ready       | toggles readiness probe           |
| /health             | returns 200 OK or 500 Error       |
| /info               | returns insights about server env |




