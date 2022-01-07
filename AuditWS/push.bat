docker rmi pasthortown/audit:http
docker rmi pasthortown/audit:https
cd E:\Proyectos\BDD MONGO ADMIN\AuditWS\
cd dockerImage\
docker build . -t pasthortown/audit:http
cd ..
cd dockerImageHttps\
docker build . -t pasthortown/audit:https
docker push pasthortown/audit:http
docker push pasthortown/audit:https