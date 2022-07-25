docker rmi pasthortown/mailer-test:http
docker rmi pasthortown/mailer-test:https
cd E:\Proyectos\BDD MONGO ADMIN\TestMailWS\
cd dockerImage\
docker build . -t pasthortown/mailer-test:http
cd ..
cd dockerImageHttps\
docker build . -t pasthortown/mailer-test:https
docker push pasthortown/mailer-test:http
docker push pasthortown/mailer-test:https