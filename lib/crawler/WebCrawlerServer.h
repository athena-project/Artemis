#ifndef WEPCRAWLERSERVER_H_INCLUDED
#define WEPCRAWLERSERVER_H_INCLUDED

#include <string>
#include <vector>
#include <utility>
#include <map>
#include <list>
#include <queue>
#include <sstream>
#include <QtNetwork>

#include <boost/serialization/string.hpp>
#include <boost/serialization/list.hpp>
#include <boost/regex.hpp>

#include "WebCrawlerNode.h"


namespace Athena{
    namespace Artemis{
        class WebCrawlerServer : public QObject{
            protected:
                QTcpServer* tcpServer;
                vector< QTcpSocket * > clients;
                unsigned int msgSize;


                vector< WebCrawlerNode* > nodes;
                int pagePerNode;

                map< string, bool > urlsMap; //urls, si l'url à déjà était visitée dans un lointain passé
                int maxUrls;

                map< string, pair< long int, unsigned char* > > visitedUrls; // url, last visit time, hash
                int refreshDelay;
                int maxVisitedUrls;

                vector< string > urlRules; //Regex
                vector< string > contentTypes;

            protected slots:
                void initCo();
                void receivedData();
                void endCo();



            public:
                WebCrawlerServer( int pagePerNode, int maxUrls, int refreshDelay, int maxVisitedUrls);
                ~WebCrawlerServer();

                void setUrlRules(vector<string> rules);
                void addUrlRules();

                vector< pair<WebCrawlerNode*,int> > getNodeByState(int state);
                pair<WebCrawlerNode*,int>   getNodeByIp( string ip);

                bool validUrl(string const& url);
                void addUrls( list< string >& urls );
                queue< pair<string,bool> > createUrlsBundle();

                void sendWork(queue< pair<string, bool> >const & urls, int nodeLocation);




                void summonToWork();


        };
    }
}

#endif // WEPCRAWLERSERVER_H_INCLUDED
