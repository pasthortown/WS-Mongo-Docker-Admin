docker rmi pasthortown/mailer:http
docker rmi pasthortown/mailer:https
cd E:\Proyectos\BDD MONGO ADMIN\MailerWS\
cd dockerImage\
docker build . -t pasthortown/mailer:http
cd ..
cd dockerImageHttps\
docker build . -t pasthortown/mailer:https
docker push pasthortown/mailer:http
docker push pasthortown/mailer:https