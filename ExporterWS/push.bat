docker rmi pasthortown/exporter:http
docker rmi pasthortown/exporter:https
cd E:\Proyectos\BDD MONGO ADMIN\ExporterWS\
cd dockerImage\
docker build . -t pasthortown/exporter:http
cd ..
cd dockerImageHttps\
docker build . -t pasthortown/exporter:https
docker push pasthortown/exporter:http
docker push pasthortown/exporter:https