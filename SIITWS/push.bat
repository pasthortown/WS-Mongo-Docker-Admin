docker rmi pasthortown/siit:http
docker rmi pasthortown/siit:https
cd E:\Proyectos\BDD MONGO ADMIN\SIITWS\
cd dockerImage\
docker build . -t pasthortown/siit:http
cd ..
cd dockerImageHttps\
docker build . -t pasthortown/siit:https
docker push pasthortown/siit:http
docker push pasthortown/siit:https
