docker rmi pasthortown/catalog-admin:http
docker rmi pasthortown/catalog-admin:https
cd E:\Proyectos\BDD MONGO ADMIN\CatalogWS\
cd dockerImage\
docker build . -t pasthortown/catalog-admin:http
cd ..
cd dockerImageHttps\
docker build . -t pasthortown/catalog-admin:https
docker push pasthortown/catalog-admin:http
docker push pasthortown/catalog-admin:https