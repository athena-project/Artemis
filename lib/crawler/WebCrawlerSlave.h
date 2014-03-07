#ifndef WEBCRAWLERSLAVE_H_INCLUDED
#define WEBCRAWLERSLAVE_H_INCLUDED


#include <queue>
#include <list>
#include <map>
#include <algorithm>    // std::find

#include "HTTPHandler"
#include "HTTPHeaderReponse"

using namespace std;


namespace Athena{
    namespace Artemis{

        class WebCrawlerSlave{
            protected:
                HTTPHandler* handler;
                queue< pair<string, bool> > urls;
                list< string > returnUrls;


                map< string, pair< long int, int> > visitedDomain; // domain, last visit time, nbr of visit the last second
                int nRQS; //numbre of requete per domain

                queue< WebRessource* > ressources;//ressources : url, contentType, data
                int ressourcesMaxSize;
                int ressourcesSize;

                pthread_mutex_t *mutex_visited;
            public:
                WebCrawlerSlave(queue< string > urls, map< string, pair< long int, int> >& visitedDomain,
pthread_mutex_t* mutex_visited, vector< string >const& contentTypes, vector< string >const& pageContentTypes);
                ~WebCrawlerSlave();

                void setNRQS( int n);
                void setPagesSize( int n);
                void setRessourcesSize( int n);
                void setContentTypes( vector<string> t );

                bool validHeader(HTTPHeaderReponse& header);
                void addUrl( list<string>const&  newUrls );

                void work();
                list< string > crawl();
                void save();
        };
    }
}

#endif // WEBCRAWLERSLAVE_H_INCLUDED
