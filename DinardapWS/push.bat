docker rmi pasthortown/dinardap:http
docker rmi pasthortown/dinardap:https
cd E:\Proyectos\BDD MONGO ADMIN\DinardapWS\
cd dockerImage\
docker build . -t pasthortown/dinardap:http
cd ..
cd dockerImageHttps\
docker build . -t pasthortown/dinardap:https
docker push pasthortown/dinardap:http
docker push pasthortown/dinardap:https
