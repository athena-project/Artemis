#ifndef WEBCRAWLERSLAVE_H_INCLUDED
#define WEBCRAWLERSLAVE_H_INCLUDED


#include <queue>
#include <list>
#include <map>
#include <algorithm>    // std::find

#include "HTTPHandler.h"
#include "Hephaistos/WebRessource.h"
#include "Hephaistos/WebRessourceHandler.h"
#include "HTTPHeaderReponse.h"

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

                Hephaistos::WebRessourceHandler* ressourceHandler;
                queue< WebRessource > ressources;//ressources : url, contentType, data
                int ressourcesMaxSize;
                int ressourcesSize;

                pthread_mutex_t *mutex_visited;
            public:
                WebCrawlerSlave(queue< pair<string,bool> > urls, map< string, pair< long int, int> >& visitedDomain,
pthread_mutex_t* mutex_visited, vector< string >const& contentTypes, vector< string >const& pageContentTypes);
                ~WebCrawlerSlave();

                void setNRQS( int n);
                void setRessourcesSize( int n);

                bool validHeader(HTTPHeaderReponse& header);
                void addUrl( list<string>&  newUrls );

                void work();
                list< string > crawl();
                void save();
        };
    }
}

#endif // WEBCRAWLERSLAVE_H_INCLUDED
