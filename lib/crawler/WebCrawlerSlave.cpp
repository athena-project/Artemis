#include "WebCrawlerSlave.h"

namespace Athena{
    namespace Artemis{

        WebCrawlerSlave::WebCrawlerSlave(queue< string > urls, map< string, pair< long int, int> >& visitedDomain,
pthread_mutex_t* mutex_visited, vector< string >const& contentTypes, vector< string >const& pageContentTypes){
            this->urls              = urls;
            this->visitedDomain     = visistedDomain;
            this->mutex_visisted    = mutex_visited;

            handler                 = new HTTPHandler(contentTypes, pageContentTypes);
            ressourcesSize          = 0;
        }

        WebCrawlerSlave::~WebCrawlerSlave(){
            delete handler;
            delete mutex_visisted;
            while( ressources.empty() ){
                delete ressources.front();
                ressources.pop();
            }
        }

        void WebCrawlerSlave::setNRQS( int n){ nRQS=n; }
        void WebCrawlerSlave::setPagesSize( int n){ pagesSize=n; }
        void WebCrawlerSlave::setRessourcesSize( int n){ ressourcesSize=n; }
        void WebCrawlerSlave::setContentTypes( vector<string> t { contentTypes=t; }

        bool WebCrawlerSlave::validHeader(HTTPHeaderReponse& header){
            if( contentTypes.size() == 0 )
                return true;

            vector<string>::iterator it = find( contentTypes.begin(), contentTypes.end(), header.getContentType() );
            if( it!=contentTypes.end() )
                return true;

            return false;
        }


        void addUrl( list<string>const&  newUrls ){
            for(list<string>::iterator it=newUrls.begin(); it!=newUrls.end() ; it++)
                returnUrls.push_back( *it );
        }

        void WebCrawlerSlave::work(){
            if( !urls.empty() )
                return;

            pair<string, bool> url = self->urls.front();
            urls.pop();

//                  if we want to check visisted domains
//                string domain = self->extractDomain( url );
//                if( !self->validUrl(url, domain) )
//                    process( self );

            pair< HTTPHeaderReponse, WebRessource* > content = self->handler->get( url.first );
            WebRessource ressource = content.second;

            if ( !validHeader( content.first ) )
                work();


            addUrl( ressource.collectURL() );

            if( sizeof(*ressource) + ressourcesSize > ressourcesMaxSize ){
                ressources.push( ressource );
                ressourcesSize=0;
                save();
            }
                ressources.push( ressource );
                ressourcesSize+=sizeof(*ressource);
                process();
        }

        list< string > WebCrawlerSlave::crawl(){
            work();
            return returnUrls;
        }

        void WebCrawlerSlave::save(){
            while( !ressources.empty() ){
                ressources.front().save(......);
                delete ressources.front();
                ressources.pop();
            }
        }
    }
}
