//#include "WebCrawler.h"
//
//namespace Athena{
//    namespace Artemis{
//
//        WebCrawler::WebCrawler(int nRQS, int maxSizePages, int numRequete, int refreshDelay, string logPath){
//            this->nRQS=nRQS;
//            this->maxSizePages=maxSizePages;
//            this->numRequete=numRequete;
//            this->refreshDelay=refreshDelay;
//            this->logPath=logPath;
//            this->pagesSize=0;
//            this->ressourcesSize=0;
//
//            handler= new HTTPHandler();
//            init();
//        }
//
//        WebCrawler::~WebCrawler(){
//            delete handler;
//        }
//
//        void WebCrawler::init(){
//            contentTypes.push_back("text/html; charset=iso-8859-1");
//            contentTypes.push_back("text/html; charset=utf-8");
//            contentTypes.push_back("text/html; charset=UTF-8");
//            hrefElements.push_back( GUMBO_TAG_A );
//            //hrefElements.push_back( GUMBO_TAG_AREA );
//        }
//
//
//        void WebCrawler::setUrlRules(vector<string> rules){
//            urlRules=rules;
//        }
//
//        void WebCrawler::setDir(string directory){
//            dir=directory;
//        }
//
//        void WebCrawler::addUrl(string const& url){
//            urls.push(url);
//        }
//
//        void WebCrawler::crawl(){
//            string page;
//            numThreads =1;
//            //Multithreading
//            pthread_t handler=pthread_t();
//            //pthread_create( &handler, NULL, &manage, this);
//
//
//            pthread_t primaryThread = pthread_t();
//            pthread_t secondaryThread = pthread_t();
//            pthread_create( &primaryThread, NULL, &process, this);
//            sleep(2);
//            pthread_create( &secondaryThread, NULL, &process, this);
//            //manage();
//            pthread_join( primaryThread, NULL);
//            /*pthread_t t[numThreads];
//            for(int i=0; i<numThreads; i++){
//                t[i]= pthread_t();
//
//
//
//            }
//            for(int i=0; i<numThreads; i++)
//                pthread_join( t[i], NULL);*/
//
//        }
//
//        void* WebCrawler::process( void* th ){
//            pthread_t cur=pthread_self();
//            cout<<"Thread n° "<<cur<<endl;
//
//            WebCrawler* self= (WebCrawler*) th;
//            if( self->urls.empty() ){
//                self->die();
//                return NULL;
//            }
//
//            string url = self->urls.front();
//            self->urls.pop();
//
////                cout<<"VisitedUrl size : "<<self->visitedUrl.size()<<endl;
////                cout<<"VisitedDomain size : "<<self->visitedDomain.size()<<endl;
////                cout<<"Url under way : "<<url<<endl;
////                cout<<"URL stack : "<<self->urls.size()<<endl;
////                cout<<"Pages stack size"<<self->pagesSize<<endl;
////                cout<<endl<<endl;
//
//
//            string domain = self->extractDomain( url );
//            if( !self->validUrl(url, domain) )
//                process( self );
//
//            pair< HTTPHeaderReponse, string > content = self->handler->get( url );
//            string page = content.second;
////            cout<<"under way"<<endl;
////             cout<<endl;
//            if ( !self->validHeader( content.first ) )
//                process( self );
////            cout<<"under way 2"<<endl;
//            unsigned char md5[MD5_DIGEST_LENGTH];
//            self->simpleMD5( (unsigned char*)page.c_str(), page.size(), md5 );
////cout<<"under way 3"<<endl;
//            //Processing only if the hash is not same than the last one or if the url has not been already visited
//            map< string, pair< long int, unsigned char* > >::iterator itVisitedUrl = self->visitedUrl.find(url);
//            if( (itVisitedUrl!= self->visitedUrl.end() && itVisitedUrl->second.second == md5) )
//                process( self );
//
//            self->collectURL(page, url, domain);
//
//            if( self->pagesSize + page.size() > self->maxSizePages ){
//                self->pagesSize=0;
//                self->savePage();
//            }
//            self->pages.push( pair<string, string>(url, page) );
//            self->pagesSize+=page.size();
//
//
//            process( self );
//        }
//
//        void WebCrawler::savePage(){
//            cout<<"saving"<<endl<<endl;
//            if(pages.empty())
//                    return;
//
//            pthread_mutex_lock( &mutex_save);
//            //pthread_cond_wait ( &cond_save, &mutex_save);
//            {
//
//
//                timeval tim;
//                gettimeofday(&tim, NULL);
//
//                ostringstream file;
//                file<<dir<<"/";
//                file<<tim.tv_sec;
//                file<<tim.tv_usec;
//                ofstream block( file.str().c_str(), ios::app );
//
//                //Header
//                block << "<block>"<<endl;
//                pair<string, string> page;
//                for(int a=0; a<pages.size(); a++){
//                   page=pages.front();
//                   pages.pop();
//
//                    block << "<page location=\"" << page.first << "\">" <<endl;
//                    block << page.second         << "</page>";
//                }
//
//                block << "</block>";
//            }
//            cout<<"end saving"<<endl;
//
//           // pthread_cond_broadcast( &cond_save );
//            pthread_mutex_unlock( &mutex_save);
//
//        }
//
//
//        bool WebCrawler::validUrl(string const& url, string const& domain){
//            bool flag=true;
//            //Default all url allowed
//            if( urlRules.size() > 0 ){
//                boost::cmatch what;
//                int i=0;
//
//                while( i<urlRules.size() && flag ){
//                    boost::regex expression( urlRules[i] );
//                    flag=boost::regex_match(url.c_str(), what, expression );
//                    i++;
//                }
//            }
//            if(!flag)
//                return false;
//
//
//
//            long int t = static_cast<long int> (time(NULL));
//            map< string, pair< long int, unsigned char* > > ::iterator itVisitedUrl = visitedUrl.find(url);
//            if( itVisitedUrl!=visitedUrl.end() && itVisitedUrl->second.first+refreshDelay>t)//Url already visited and delay not over
//                return false;
//
//
//            map< const string, pair< long int, int> >::iterator itVisitedDomain = visitedDomain.find(url);
//            if( itVisitedDomain!=visitedDomain.end() && itVisitedDomain->second.first+nRQS>t){//Too many requete for this domain
//                urls.push(url);
//                return false;
//            }
//
//            pthread_mutex_lock( &mutex_visited );
//            {
//                //Update visitedUrl and visitedDomain
//                if(itVisitedDomain!=visitedDomain.end()){
//                    if(itVisitedDomain->second.first==t)
//                        itVisitedDomain->second.second++;
//                    else{
//                         itVisitedDomain->second.first  = t;
//                         itVisitedDomain->second.second = 1;
//                    }
//                }else
//                    visitedDomain.insert( pair< const string, pair< long int, int> >(
//                                                domain, pair< long int, int>(t, 1)
//                                        ) );
//
//
//
//                if(itVisitedUrl!=visitedUrl.end())
//                    itVisitedUrl->second.first=t;
//                else
//                    visitedUrl.insert(  pair< string, pair< long int, unsigned char*>  >(
//                                            url, pair< long int, unsigned char* > (t, NULL)
//                                        ) );
//            }
//            pthread_mutex_unlock( &mutex_visited );
//
//            return true;
//        }
//
//        bool WebCrawler::validHeader(HTTPHeaderReponse& header){
//            if( contentTypes.size() == 0 )
//                throw "uninitialised content-type";
//
//            vector<string>::iterator it = find( contentTypes.begin(), contentTypes.end(), header.getContentType() );
//            if( it!=contentTypes.end() )
//                return true;
//
//            return false;
//        }
//
//        void WebCrawler::collectURL(string const& page, string const& currentUrl, string const& domain){
//            GumboOutput* output = gumbo_parse(page.c_str());
//            list< string > links;
//
//            fetchLinks(output->root, links);
//            addUrlFromLinks(links, currentUrl, domain);
//            gumbo_destroy_output(&kGumboDefaultOptions, output);
//        }
//
//        void WebCrawler::fetchLinks(GumboNode* node, list< string >& links){
//            if (node->type != GUMBO_NODE_ELEMENT)
//                return;
//
//            GumboAttribute* href;
//            vector<int>::iterator it1= find( hrefElements.begin(), hrefElements.end(), node->v.element.tag );
//            if ( it1 != hrefElements.end() && ( href = gumbo_get_attribute(&node->v.element.attributes, "href") ) ){
//                links.push_back( href->value );
//            }
//
//            /*GumboAttribute* src;
//            vector<int>::iterator it2= find( srcElements.begin(), srcElements.end(), node->v.element.tag );
//            if ( it1 != srcElements.end() && ( src = gumbo_get_attribute(&node->v.element.attributes, "src") ) ){
//                links.push_back( src->value );
//            }*/
//
//
//
//            GumboVector* children = &node->v.element.children;
//            for (int i = 0; i < children->length; ++i) {
//                fetchLinks(static_cast<GumboNode*>(children->data[i]), links);
//            }
//        }
//
//        void WebCrawler::addUrlFromLinks(list< string > links, string const& currentUrl, string const& currentDomain){
//            string dir=extractDir(currentUrl);
//            string protocol("");
//            string url("");
//
//            for(list< string >::iterator it=links.begin(); it!=links.end(); it++ ){
//                protocol=(*it).substr(0, 7 /*protocol.find_first_of('/')+1 */);//Https
//                if( protocol == "https://" || protocol == "http://" )
//                    url = (*it);
//                else if( protocol[0] == '/' && protocol[1] == '/' ){
//                    url = protocol.substr(0, protocol.size()-2 ) + (*it);
//                }else
//                    if( protocol[0] == '/' ){
//                        url = currentDomain + (*it).substr(1, (*it).size());
//                    }else
//                        url = dir + (*it);
//
//                urls.push( url );
//            }
//        }
//
//
//
//        string WebCrawler::extractDir(string const& url){
//            string dir(url);
//            dir=dir.substr( 0, 1 + dir.find_last_of('/') );
//            if(dir == "http://" || dir == "https://")
//                dir=url+"/";
//            return dir.c_str();
//        }
//
//        string WebCrawler::extractDomain(string const& url){
//            string domain(url);
//            int protocolEnd(0);
//
//            protocolEnd=domain.find_first_of("//");// http://
//            domain = domain.substr( 0, domain.find_first_of('/', protocolEnd+2) );
//
//            if( (*domain.end()) !='/' )
//                domain+="/";
//
//            return domain;
//        }
//
//
//        bool WebCrawler::simpleSHA256(void* input, unsigned long length, unsigned char* md){
//            SHA256_CTX context;
//            if(!SHA256_Init(&context))
//                return false;
//
//            if(!SHA256_Update(&context, (unsigned char*)input, length))
//                return false;
//
//            if(!SHA256_Final(md, &context))
//                return false;
//
//            return true;
//        }
//
//        bool WebCrawler::simpleMD5(void* input, unsigned long length, unsigned char* md){
//            MD5_CTX context;
//            if(!MD5_Init(&context))
//                return false;
//
//            if(!MD5_Update(&context, (unsigned char*)input, length))
//                return false;
//
//            if(!MD5_Final(md, &context))
//                return false;
//
//            return true;
//        }
//
//
//        void WebCrawler::log(int errorCode, string description){
//            ofstream logFile( logPath.c_str(), ios::app);
//
//            if(logFile)
//                logFile<<time(NULL)<<" "<<errorCode<<" "<<description<<endl;
//        }
//
//         //Thread manager
//        void WebCrawler::manage(){
//            //pthread_mutex_lock( &mutex_manage15 );
//
//            {
//                int maxThreads = 10;
//                int neededThreads=0;
//
//                while( !urls.empty() ){
//                    cout<<"Managing under way"<<endl;
//                    neededThreads = urls.size() / 1000;
//                    cout<<"neededThreads  "<<neededThreads<<endl;
//                    cout<<"numThreads  "<<numThreads<<endl;
//                    cout<<endl<<endl;
//
//
//                    {
//
//                        if( numThreads == 1){
//                            pthread_t tmp;
//                            pthread_create( &tmp, NULL, &process, this);
//                            numThreads++;
//                        }
//                        /*while( numThreads < maxThreads && numThreads < neededThreads ){
//                            tmp = pthread_t();
//                            pthread_create( &tmp, NULL, &process, this);
//                            numThreads++;
//                        }*/
//                    }
//                    sleep(2);
//                }
//            }
//           // pthread_mutex_unlock( &mutex_manage15 );
//
//
//            /**/
//        }
//
//        //fct appelée à la mort d'un processus
//        void WebCrawler::die(){
//            numThreads--;
//        }
//    }
//}
