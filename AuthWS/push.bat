docker rmi pasthortown/auth:http
docker rmi pasthortown/auth:https
cd E:\Proyectos\BDD MONGO ADMIN\AuthWS\
cd dockerImage\
docker build . -t pasthortown/auth:http
cd ..
cd dockerImageHttps\
docker build . -t pasthortown/auth:https
docker push pasthortown/auth:http
docker push pasthortown/auth:https
