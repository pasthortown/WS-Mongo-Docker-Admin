docker rmi pasthortown/file-admin:http
docker rmi pasthortown/file-admin:https
cd E:\Proyectos\BDD MONGO ADMIN\FileWS\
cd dockerImage\
docker build . -t pasthortown/file-admin:http
cd ..
cd dockerImageHttps\
docker build . -t pasthortown/file-admin:https
docker push pasthortown/file-admin:http
docker push pasthortown/file-admin:https