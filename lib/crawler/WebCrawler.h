#ifndef CRAWLER_H_INCLUDED
#define CRAWLER_H_INCLUDED


#include <map>
#include <list>
#include <queue>
#include <string>
#include <vector>
#include <algorithm>    // std::find
#include <utility>
#include <sys/time.h>
#include <ctime>
#include <iostream>
#include <fstream>


#include <pthread.h>

#include <boost/regex.hpp>

#include <openssl/crypto.h> //Hash function
#include <openssl/sha.h> //Hash function
#include <openssl/md5.h> //Hash function

#include "gumbo.h"
#include "HTTPHandler.h"
#include "HTTPHeaderReponse.h"


using namespace std;

namespace Athena{
    namespace Artemis{

        class WebCrawler{
            protected :
                HTTPHandler* handler;

                queue< string > urls;
                queue< pair<string, string> > pages; // url, page
                queue< pair<string, pair<string, string> > > ressources;//ressources : url, contentType, data
                int pagesSize;
                int ressourcesSize;

                map< string, pair< long int, unsigned char* > > visitedUrl; // url, last visit time, hash
                map< string, pair< long int, int> > visitedDomain; // domain, last visit time, nbr of visit the last second

                int nRQS; //numbre of requete per domain
                int maxSizePages;
                int numRequete; //Nombre de reqête simultanée ..
                int refreshDelay;

                string dir; //Ou on enregistre les pages
                string logPath;

                vector< string > urlRules; //Regex
                vector< string > contentTypes;
                vector< int > hrefElements;
                vector< int > srcElements;


                pthread_t* threads;

                pthread_mutex_t mutex_save;
                pthread_mutex_t mutex_visited;

                pthread_cond_t cond_save;
                pthread_cond_t cond_process;
                int numThreads;

            public :

                WebCrawler(int nRQS, int maxSizePages, int numRequete, int refreshDelay, string logPath);
                ~WebCrawler();
                void init();
                void setUrlRules(vector<string> rules);
                void setDir(string directory);
                void addUrl(string const& url);

                void crawl();
                static void* process( void* nul );
                void savePage();

                void collectURL(string const& page, string const& currentUrl, string const& domain);
                void fetchLinks(GumboNode* node, list<string>& links);
                void addUrlFromLinks(list<string> links, string const& currentUrl, string const& currentDomain);

                bool validUrl(string const& url, string const& domain);
                bool validHeader(HTTPHeaderReponse& header);

                string extractDomain(string const& url);
                string extractDir(string const& url);

                bool simpleSHA256(void* input, unsigned long length, unsigned char* md);
                bool simpleMD5(void* input, unsigned long length, unsigned char* md);

                void log(int errorCode, string description);

                void manage();
                void die();
        };
    }
}

#endif // CRAWLER_H_INCLUDED
