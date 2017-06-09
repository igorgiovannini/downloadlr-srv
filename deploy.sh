docker stop downloadlr-srv
docker rm downloadlr-srv
docker rmi downloadlr-srv

docker build -t downloadlr-srv .
docker run -p 34567:80 --name downloadlr-srv downloadlr-srv
