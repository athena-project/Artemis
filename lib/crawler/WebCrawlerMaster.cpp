#include "WebCrawlerMaster.h"

namespace Athena{
    namespace Artemis{

        WebCrawlerMaster::WebCrawlerMaster(string confLocation, string ip, int port){ //Conlocation chemin du repertoire arent fini sans /
            conf = new Config( confLocation+"/webcrawlermaster.conf" );
            conf->parse();
            contentTypes = conf->parseMono(confLocation+"/contentTypes");
            pageContentTypes = conf->parseMono(confLocation+"/pageContentTypes");


            this->ip=ip;
            this->port=port;

            socket = new QTcpSocket(this);
            connect(socket, SIGNAL(readyRead()), this, SLOT(receivedData()));
            connect(socket, SIGNAL(connected()), this, SLOT(connecte()));
            connect(socket, SIGNAL(disconnected()), this, SLOT(deconnecte()));
            connect(socket, SIGNAL(error(QAbstractSocket::SocketError)), this, SLOT( socketError(QAbstractSocket::SocketError) ) );
            msgSize = 0;

            socket->connectToHost( QString(ip.c_str()), port);
        }

        WebCrawlerMaster::~WebCrawlerMaster(){
            delete socket;
            delete conf;
        }

        /**
                Network
        **/
        void WebCrawlerMaster::sendData(){
            //Serialisation à faire
            /*stringstream stream;
            boost::archive::text_oarchive archive( stream );
            archive << returnUrls;*/

            QByteArray paquet;
            QDataStream out(&paquet, QIODevice::WriteOnly);

            out << (unsigned int) 0;
            //out << stream.str();
            out.device()->seek(0);
            out << (unsigned int) (paquet.size() - sizeof( unsigned int ) );

            socket->write(paquet);
        }

        void WebCrawlerMaster::connecte(){
            sendData(); //Init la connexion
        }

        void WebCrawlerMaster::receivedData(){
            QDataStream in(socket);
            if (msgSize == 0){
                if (socket->bytesAvailable() < (int)sizeof(unsigned int)) //Header constitué de la taille du message un unsigned int
                    return;
                in >> msgSize; // Si on a reçu la taille du message en entier, on la récupère
            }

            if (socket->bytesAvailable() < msgSize) // Si on n'a pas encore tout reçu, on arrête la méthode
                return;

            //Sérialisation à faire
           /* string msg;
            in >> msg;

            std::stringstream stream();
            stream << msg;
            boost::archive::text_iarchive archive(stream);
            stream >> urls;*/

            msgSize=0;
        }

        void WebCrawlerMaster::deconnecte(){

        }

        void WebCrawlerMaster::socketError(QAbstractSocket::SocketError error){
            string buffer;
            switch(error)
            {
                case QAbstractSocket::HostNotFoundError:
                    buffer = "Error host not found.";
                    break;
                case QAbstractSocket::ConnectionRefusedError:
                    buffer = "Error connection refused by the server.";
                    break;
                case QAbstractSocket::RemoteHostClosedError:
                    buffer = "Error closed connections.";
                    break;
                default:
                    buffer = "Error";
            }
            throw buffer; //a mettre ddans les logs
        }


        /**
            Threads
        **/
        queue< pair<string,bool> > WebCrawlerMaster::createUrlsBundle(){
            queue< pair<string,bool> > bundle;
            int i=0;

            while( i < urlsPerThread && !urls.empty() ){
                bundle.push( urls.front() );
                urls.pop();
                i++;
            }
            return bundle;
        }

        void* WebCrawlerMaster::newSlave( void* t ){
            WebCrawlerMaster* self= (WebCrawlerMaster*) t;

            WebCrawlerSlave slave( self->createUrlsBundle(), (self->visitedDomain), &(self->mutex_visited), self->contentTypes, self->pageContentTypes);
            list< string > tmpUrls = slave.crawl();

            pthread_mutex_lock( &(self->mutex_return) );
            for( list< string >::iterator it = tmpUrls.begin(); it!=tmpUrls.end(); it++ )
                self->returnUrls.push_back( *it );
            pthread_mutex_unlock( &(self->mutex_return) );
        }

        void WebCrawlerMaster::harness(){
                int neededThreads=0;

                while( true ){
                    neededThreads = urls.size() / urlsPerThread;


                        while( numThreads < maxThreads && numThreads < neededThreads ){
                            pthread_t tmp;
                            pthread_create( &tmp , NULL, &newSlave, this);
                            numThreads++;
                        }
                    }
                    sleep(5);
        }

    }
}
