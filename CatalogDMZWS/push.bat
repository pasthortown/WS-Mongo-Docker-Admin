docker rmi pasthortown/catalog-dmz-admin:http
docker rmi pasthortown/catalog-dmz-admin:https
cd E:\Proyectos\BDD MONGO ADMIN\CatalogDMZWS\
cd dockerImage\
docker build . -t pasthortown/catalog-dmz-admin:http
cd ..
cd dockerImageHttps\
docker build . -t pasthortown/catalog-dmz-admin:https
docker push pasthortown/catalog-dmz-admin:http
docker push pasthortown/catalog-dmz-admin:https
