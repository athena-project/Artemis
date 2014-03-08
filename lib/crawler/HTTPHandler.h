#ifndef HTTPHANDLER_H_INCLUDED
#define HTTPHANDLER_H_INCLUDED

#include <iostream>
#include <string>
#include <sstream>
#include <utility>
#include <vector>
#include <time.h>

#include </usr/include/curl/curl.h>

#include "HTTPHeaderReponse.h"
#include "Hephaistos/WebRessource.h"



using namespace std;
using namespace Athena::Hephaistos;

namespace Athena{
    namespace Artemis{

        class HTTPHandler{
            protected :
                CURL* session;
                string page;
                string userAgent;

                vector< string > contentTypes;
                vector< string > pageContentTypes;
            public :

                HTTPHandler(vector< string >const& contentTypes, vector< string >const& pageContentTypes, string agent="");

                bool validHeader(HTTPHeaderReponse& header);
                pair< HTTPHeaderReponse, Hephaistos::WebRessource > get(string const& url);
                static size_t writeInString ( void *contents, size_t size, size_t nmemb, void *userdata);

        };
    }
}

#endif // HTTPHANDLER_H_INCLUDED
