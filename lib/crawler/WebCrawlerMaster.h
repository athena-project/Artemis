#ifndef WEBCRAWLERMASTER_H_INCLUDED
#define WEBCRAWLERMASTER_H_INCLUDED

#include <map>
#include <list>
#include <queue>
#include <string>
#include <vector>
#include <algorithm>    // std::find
#include <utility>
#include <sys/time.h>
#include <ctime>
#include <iostream>

#include <QtNetwork>

#include <pthread.h>

#include "WebCrawlerSlave.h"
#include "Hephaistos/Config.h"

using namespace std;
using namespace Athena::Hephaistos;

namespace Athena{
    namespace Artemis{

        class WebCrawlerMaster : public QObject{
            protected:
                string ip;
                int port;
                QTcpSocket *socket; // Représente le serveur
                unsigned int msgSize;

                Config* conf;
                vector< string > contentTypes;
                vector< string > pageContentTypes;

                int numThreads;
                int maxThreads;
                int urlsPerThread;
                pthread_mutex_t mutex_return;
                pthread_mutex_t mutex_visited;

                map< string, pair< long int, int> > visitedDomain; // domain, last visit time, nbr of visit the last second
                queue< pair<string, bool> > urls;
                list< string > returnUrls;

            protected slots:
                void connecte();
                void receivedData();
                void deconnecte();
                void socketError(QAbstractSocket::SocketError error);

            public:
                WebCrawlerMaster(string confLocation, string ip, int port);
                ~WebCrawlerMaster();

                queue< pair<string,bool> > createUrlsBundle();

                static void* newSlave( void* t );
                void harness();
                void sendData();
        };

    }

}

#endif // WEBCRAWLERMASTER_H_INCLUDED
