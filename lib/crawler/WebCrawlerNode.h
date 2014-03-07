#ifndef WEBCRAWLERNODE_H_INCLUDED
#define WEBCRAWLERNODE_H_INCLUDED

#include <string>

using namespace std;

namespace Athena{
    namespace Artemis{

        class WebCrawlerNode{
            protected :
                string ip;
                int port;
                int state;

            public :
                enum state{ AVAILABLE, PROCESSING, LOST };
                WebCrawlerNode();
                WebCrawlerNode(string ip, int port, int state = AVAILABLE );

                string setIp( string i);
                int setPort( int p);
                int setState( int s);

                string getIp();
                int getPort();
                int getState();

                bool isAvailable();
        };

    }

}

#endif // WEBCRAWLERNODE_H_INCLUDED
