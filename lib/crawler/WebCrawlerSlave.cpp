#include "WebCrawlerSlave.h"

namespace Athena{
    namespace Artemis{

        WebCrawlerSlave::WebCrawlerSlave(queue< pair<string,bool> > urls, map< string, pair< long int, int> >& visitedDomain,
pthread_mutex_t* mutex_visited, vector< string >const& contentTypes, vector< string >const& pageContentTypes){
            this->urls              = urls;
            this->visitedDomain     = visitedDomain;
            this->mutex_visited    = mutex_visited;

            handler                 = new HTTPHandler(contentTypes, pageContentTypes);
            ressourcesSize          = 0;
        }

        WebCrawlerSlave::~WebCrawlerSlave(){
            delete handler;
            delete mutex_visited;
        }

        void WebCrawlerSlave::setNRQS( int n){ nRQS=n; }
        void WebCrawlerSlave::setRessourcesSize( int n){ ressourcesSize=n; }


        void WebCrawlerSlave::addUrl( list<string>&  newUrls ){
            for(list<string>::iterator it=newUrls.begin(); it!=newUrls.end() ; it++)
                returnUrls.push_back( *it );
        }

        void WebCrawlerSlave::work(){
            if( !urls.empty() )
                return;

            pair<string, bool> url = urls.front();
            urls.pop();

//                  if we want to check visisted domains
//                string domain = self->extractDomain( url );
//                if( !self->validUrl(url, domain) )
//                    process( self );

            pair< HTTPHeaderReponse, WebRessource > content = handler->get( url.first );
            WebRessource ressource = content.second;

            if ( content.second.empty() )
                work();

            list<string> newUrls=ressource.collectURL();
            addUrl( newUrls );

            if( sizeof(ressource) + ressourcesSize > ressourcesMaxSize ){
                ressources.push( ressource );
                ressourcesSize=0;
                save();
            }
                ressources.push( ressource );
                ressourcesSize+=sizeof(ressource);
                work();
        }

        list< string > WebCrawlerSlave::crawl(){
            work();
            return returnUrls;
        }

        void WebCrawlerSlave::save(){
            while( !ressources.empty() ){
                ressourceHandler->save( ressources.front() );
                ressources.pop();
            }
        }
    }
}
