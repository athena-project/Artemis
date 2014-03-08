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
            if ( !tcpServer->listen(QHostAddress::Any, 33755) ){
                throw "error server ";
            }
            connect(tcpServer, SIGNAL(newConnection()), this, SLOT(initCo()));
        }

        WebCrawlerServer::~WebCrawlerServer(){
            delete tcpServer;
            for(int i=0; i<clients.size(); i++ ){//same number of client and node
                delete clients[i];
                delete nodes[i];
            }
        }

        /**
                Divers
        **/
        vector< pair<WebCrawlerNode*,int> > WebCrawlerServer::getNodeByState(int state){
            vector< pair<WebCrawlerNode*,int> >  currentNodes;
            for(int i=0; i<nodes.size(); i++){
                if( nodes[i]->isAvailable() ){
                   currentNodes.push_back(  make_pair(nodes[i], i) );
                }
            }
            return currentNodes;
        }

        pair<WebCrawlerNode*,int>  WebCrawlerServer::getNodeByIp( string ip){
            for(int i=0; i<nodes.size(); i++)
                if(nodes[i]->getIp() == ip)
                    return pair<WebCrawlerNode*,int>(nodes[i],i);

            return pair<WebCrawlerNode*,int> (NULL,0);
        }

        /**
                Network
        **/

        void WebCrawlerServer::initCo(){
            QTcpSocket *socket = tcpServer->nextPendingConnection();
            clients.push_back( socket );
            connect( socket, SIGNAL(readyRead()), this, SLOT(receivedData()));
            connect( socket, SIGNAL(disconnected()), this, SLOT(endCo()));

            nodes.push_back( new WebCrawlerNode( socket->peerAddress().toString().toStdString(), (int)socket->localPort(), WebCrawlerNode::AVAILABLE ) );
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


            //Serialisation à faire soit qt, soit boost, soit à la main ici et dans master
            /*QString msg;
            in >> msg;

            list< string > tmpUrls;
            QDataStream out;
            ostringstream stream;
            stream << 1;//(msg.toStdString()) ;
            boost::archive::text_iarchive archive(stream.str());
            stream >> urls;
            addUrls( urls );*/

            msgSize=0;
    }

        void WebCrawlerServer::endCo(){
            QTcpSocket *socket = qobject_cast<QTcpSocket *>(sender());
            if (socket == 0) // Si par hasard on n'a pas trouvé le client à l'origine du signal, on arrête la méthode
                return;

            string ip = socket->peerAddress().toString().toStdString();

            for(int i=0 ; i < nodes.size(); i++ ){
                if(nodes[i]->getIp() == ip){
                    nodes.erase( nodes.begin() + i );
                    delete clients[i];
                    clients.erase( clients.begin() + i );
                }
            }

            socket->deleteLater();
        }

        void WebCrawlerServer::sendWork(queue< pair<string, bool> >const & urls, int nodeLocation){
            /*de même serialisation
             *stringstream stream;
            boost::archive::text_oarchive archive( stream );
            archive << urls;*/


             // Préparation du paquet
            QByteArray paquet;
            QDataStream out(&paquet, QIODevice::WriteOnly);

            out << (unsigned int) 0; // On écrit 0 au début du paquet pour réserver la place pour écrire la taille
            //out << stream.str(); // On ajoute le message à la suite
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
            map< string, pair< long int, unsigned char* > > ::iterator itVisitedUrl = visitedUrls.find(url);
            if( itVisitedUrl!=visitedUrls.end() && itVisitedUrl->second.first+refreshDelay>t)//Url already visited and delay not over
                return false;




            if(itVisitedUrl!=visitedUrls.end())
                itVisitedUrl->second.first=t;
            else if( visitedUrls.size() <= maxVisitedUrls )
                visitedUrls.insert(  pair< string, pair< long int, unsigned char*>  >(
                                    url, pair< long int, unsigned char* > (t, NULL)
                                ) );
            return true;
        }


        void WebCrawlerServer::addUrls( list< string >  &urls ){
            for( list< string >::iterator it = urls.begin() ; it != urls.end() ; it++ )
                if( validUrl(*it) && urlsMap.size() <= maxUrls )
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
            vector< pair<WebCrawlerNode*, int> > availableNodes = getNodeByState( WebCrawlerNode::AVAILABLE ); //int => ordre dans le tableau ie mêm ordre pr les sockets
            int i=0;
            while( i<availableNodes.size() && !urlsMap.empty() ){
                sendWork( createUrlsBundle(), availableNodes[i].second );
            }
        }

    }
}
