#include "HTTPHandler.h"

namespace Athena{
    namespace Artemis{

        HTTPHandler::HTTPHandler(vector< string >const& contentTypes, vector< string >const& pageContentTypes, string agent){
            this->contentTypes=contentTypes;
            this->pageContentTypes=pageContentTypes;
            this->userAgent=agent;
        }
        /*
         * @param : ptr
         */

        size_t HTTPHandler::writeInString ( void *contents, size_t size, size_t nmemb, void *userdata){
            ((string*)userdata)->append((char*)contents, size * nmemb);
            return size * nmemb;
        }

        bool HTTPHandler::validHeader(HTTPHeaderReponse& header){
            if( contentTypes.size() == 0 )
                return true;

            vector<string>::iterator it = find( contentTypes.begin(), contentTypes.end(), header.getContentType() );
            if( it!=contentTypes.end() )
                return true;

            return false;
        }

        pair< HTTPHeaderReponse, Hephaistos::WebRessource > HTTPHandler::get(string const& url){
            string buffer;
            string headerBuffer;
            HTTPHeaderReponse header;
            CURLcode result;
            session = curl_easy_init();
            curl_easy_setopt(session, CURLOPT_TIMEOUT, 2 );
            curl_easy_setopt(session, CURLOPT_DNS_SERVERS, "8.8.8.8;8.8.4.4;208.67.222.222;208.67.222.220" ); //2 premiers google, 2 autres opendns

            if(session){ //gestion des erreurs à faire
                if( userAgent!="" )
                    curl_easy_setopt(session, CURLOPT_USERAGENT, userAgent.c_str() );

                curl_easy_setopt(session, CURLOPT_URL, url.c_str() );

                curl_easy_setopt(session,  CURLOPT_HEADERDATA, &headerBuffer);

                curl_easy_setopt(session,  CURLOPT_WRITEDATA, &buffer);
                curl_easy_setopt(session,  CURLOPT_WRITEFUNCTION, writeInString);

                result = curl_easy_perform(session);
                curl_easy_cleanup(session);
            }

            header.parse(headerBuffer);
            if((CURLE_OK == result) && validHeader(header)){
                return pair< HTTPHeaderReponse, WebRessource >( header , WebRessource( (string)url, header.getContentType(), sizeof(buffer), buffer, (unsigned int)time(NULL) ) );
            }else{
                ofstream logFile( "HTTPHandler.log", ios::app);
                logFile<<curl_easy_strerror(result)<<"    "<<url<<endl;
                return pair< HTTPHeaderReponse, WebRessource >( header, WebRessource() );
            }

        }
    }
}
