#ifndef HTTPHANDLER_H_INCLUDED
#define HTTPHANDLER_H_INCLUDED

#include <iostream>
#include <string>
#include <sstream>
#include <utility>
#include "HTTPHeaderReponse.h"
#include </usr/include/curl/curl.h>




using namespace std;

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
                pair< HTTPHeaderReponse, string > get(string const& url);
                static size_t writeInString ( void *contents, size_t size, size_t nmemb, void *userdata);

        };
    }
}

#endif // HTTPHANDLER_H_INCLUDED
