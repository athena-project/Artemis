#include "WebCrawlerServer.h"


namespace Athena{
    namespace Artemis{
        WebCrawlerServer::WebCrawlerServer( int pagePerNode, int maxUrls, int refreshDelay, int maxVisitedUrls){
            this->pagePerNode       = pagePerNode;
            this->maxUrls           = maxUrls;
            this->refreshDelay      = refreshDelay;
            this->maxVisitedUrls    = maxVisitedUrls;



            //Tcp server
            msgSize = 0;
            tcpServer = new QTcpServer(this);
            if ( !serveur->listen(QHostAddress::Any, 33755) ){
                throw "error server "
            }
            connect(tcpServer, SIGNAL(newConnection()), this, SLOT(initCo()));
        }

        ~WebCrawlerServer(){
            delete [] tcpServer;
            delete [] nodes;
        }

        /**
                Divers
        **/
        vector< WebCrawlerNode* > getNodeByState(int state){
            vector< WebCrawlerNode* >  currentNodes;
            for(int i=0; i<nodes.size(); i++){
                if( nodes[i]->isAvailable() )
                    currentNodes.push_back( nodes[i] );
            }
            return currentNodes;
        }
        WebCrawlerNode*  getNodeByIp( string ip){
            for(int i=0; i<nodes.size(); i++)
                if(nodes[i]->getIp() == ip)
                    return nodes[i];

            return WebCrawlerNode();
        }

        /**
                Network
        **/

        void WebCrawlerServer::initCo(){
            QTcpSocket *socket = tcpServer->nextPendingConnection();
            clients.push_back( socket );
            connect( socket, SIGNAL(readyRead()), this, SLOT(receivedData()));
            connect( socket, SIGNAL(disconnected()), this, SLOT(endCo()));

            nodes.push_back( new WebCrawlerNode( socket->localAdress().toString().toStlString(), (int)socket->localPort(), WebCrawlerNode::AVAILABLE ) );
        }

        void WebCrawlerServer::receivedData(){
            QTcpSocket *socket = qobject_cast<QTcpSocket *>(sender());
            if (socket == 0) // Si par hasard on n'a pas trouvé le client à l'origine du signal, on arrête la méthode
                return;

            QDataStream in(socket);
            if (msgSize == 0){
                if (socket->bytesAvailable() < (int)sizeof(unsigned int)) //Header constitué de la taille du message un unsigned int
                    return;
                in >> msgSize; // Si on a reçu la taille du message en entier, on la récupère
            }

            if (socket->bytesAvailable() < msgSize) // Si on n'a pas encore tout reçu, on arrête la méthode
                return;

            string msg;
            in >> msg;

            list< string > urls;
            std::stringstream stream();
            stream << msg;
            boost::archive::text_iarchive archive(stream);
            stream >> urls;
            addUrls( urls );

            msgSize=0;
    }

        void WebCrawlerServer::endCo(){
            QTcpSocket *socket = qobject_cast<QTcpSocket *>(sender());
            if (socket == 0) // Si par hasard on n'a pas trouvé le client à l'origine du signal, on arrête la méthode
                return;

            string ip = socket->localAdress().toString().toStlString();
            int i=0;

            while( i < nodes.size() ){
                if(nodes[i]->getIp() == url){
                    nodes.erase( nodes.begin() + i );
                    i= nodes.size();
                }
                i++;
            }

            clients.removeOne(socket);
            socket->deleteLater();
        }

        void WebCrawlerServer::sendWork(list< string >const & urls, int nodeLocation){
            stringstream stream;
            boost::archive::text_oarchive archive( stream );
            archive << urls;


             // Préparation du paquet
            QByteArray paquet;
            QDataStream out(&paquet, QIODevice::WriteOnly);

            out << (unsigned int) 0; // On écrit 0 au début du paquet pour réserver la place pour écrire la taille
            out << stream.str(); // On ajoute le message à la suite
            out.device()->seek(0); // On se replace au début du paquet
            out << (unsigned int) (paquet.size() - sizeof(unsigned int)); // On écrase le 0 qu'on avait réservé par la longueur du message


            // Envoi du paquet préparé à tous les clients connectés au serveur
            QTcpSocket* client=clients[nodeLocation]; //car même indice
            client->write(paquet );
        }


        /**
                Node Handler
        **/
        bool WebCrawlerServer::validUrl(string const& url){
            bool flag=true;

            //Default all url allowed
            if( urlRules.size() > 0 ){
                boost::cmatch what;
                int i=0;

                while( i<urlRules.size() && flag ){
                    boost::regex expression( urlRules[i] );
                    flag=boost::regex_match(url.c_str(), what, expression );
                    i++;
                }
                if(!flag)
                    return false;
            }




            long int t = static_cast<long int> (time(NULL));
            map< string, pair< long int, unsigned char* > > ::iterator itVisitedUrl = visitedUrl.find(url);
            if( itVisitedUrl!=visitedUrl.end() && itVisitedUrl->second.first+refreshDelay>t)//Url already visited and delay not over
                return false;




            if(itVisitedUrl!=visitedUrl.end())
                itVisitedUrl->second.first=t;
            else if( visitedUrls.size() <= maxVisitedUrls )
                visitedUrl.insert(  pair< string, pair< long int, unsigned char*>  >(
                                    url, pair< long int, unsigned char* > (t, NULL)
                                ) );
            return true;
        }


        void WebCrawlerServer::addUrls( list< string > const &urls ){
            for( list< string >::iterator it = urls.begin() ; it != urls.end() ; it++ )
                if( validUrl(*it) && urlsMaps.size() <= maxUrls )
                    urlsMap[ *it ] = true;
        }

        queue< pair<string, bool> > WebCrawlerServer::createUrlsBundle(){
            queue< pair<string, bool> > bundle;
            int i=0;

            while( i < pagePerNode && !urlsMap.empty() ){
                bundle.push( *urlsMap.begin() );
                urlsMap.erase( urlsMap.begin() );
                i++;
            }
            return bundle;
        }

        void WebCrawlerServer::summonToWork(){
            vector< pair<WebCrawlerNode, int> > availableNodes = getNodeByState( WebCrawlerNode::AVAILABLE ); //int => ordre dans le tableau ie mêm ordre pr les sockets
            int i=0;
            while( i<availableNodes.size() && !urlsMap.empty() ){
                sendWork( createUrlsBundle(), availableNodes[i].second );
            }
        }

    }
}
