#ifndef WEPCRAWLERSERVER_H_INCLUDED
#define WEPCRAWLERSERVER_H_INCLUDED

#include <string>
#include <vector>
#include <map>
#include <list>
//#include <QtNetwork>

#include <boost/archive/text_oarchive.hpp>
#include <boost/archive/text_iarchive.hpp>

//#include "WebCrawlerNode.h"


namespace Athena{
    namespace Artemis{
        class WebCrawlerServer{
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

                vector< WebCrawlerNode* > getNodeByState(int state);
                WebCrawlerNode*  getNodeByIp( string ip);

                bool validUrl(string const& url)
                void addUrls( list< string > const &urls );
                list< string > createUrlsBundle();

                void sendWork(list< string >const & urls);




                void summonToWork();


        };
    }
}

#endif // WEPCRAWLERSERVER_H_INCLUDED
