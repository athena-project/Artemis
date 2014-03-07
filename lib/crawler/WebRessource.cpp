#include "WebRessource.h"

namespace Athena{
    namespace Artemis{

        WebRessource::WebRessource(){}

        WebRessource::WebRessource(string url, string contentType, unsigned int size, string content, unsigned int modified){
            setUrl( url );
            setContent( contentType );
            setSize( size );
            setContent( content );
            setModified( modified );
            type = WebRessources::DEFAULT;
        }

        WebRessource::WebRessource(unsigned int id, string url, string contentType, unsigned int size, string content, unsigned int modified){
            WebRessource(url, contentType, size, content, modified);
            setId( id );


        }


        int WebRessource::getId(){ return id; }
        string WebRessource::getUrl(){ return url; }
        string WebRessource::getContentType(){ return contentType; }
        unsigned int WebRessource::getSize(){ return size; }
        string WebRessource::getContent(){ return content; }
        unsigned int WebRessource::getModified(){ return modified; }

        void WebRessource::setId(int param){ id = param; }
        void WebRessource::setUrl(string param){ url = param; }
        void WebRessource::setContentType(string param){ contentType = param; }
        void WebRessource::setSize(unsigned int param){ size = param; }
        void WebRessource::setContent(string param){ content = param; }
        void WebRessource::setModified(unsigned int param){ modified = param; }


        string WebRessource::extractDir(){
            dir=dir.substr( 0, 1 + dir.find_last_of('/') );
            if(dir == "http://" || dir == "https://")
                dir=url+"/";
            return dir;
        }

        string WebRessource::extractDomain(){
            int protocolEnd(0);

            protocolEnd=domain.find_first_of("//");// http://
            domain = domain.substr( 0, domain.find_first_of('/', protocolEnd+2) );

            if( (*domain.end()) !='/' )
                domain+="/";

            return domain;
        }



        list<string> WebRessource::collectURL( ){
            return list<string>();
        }

        void WebRessource::fetchLinks(GumboNode* node, list< string >& links){}

        list< string > WebRessource::urlFromLinks(list< string >& links){}

    }
}
