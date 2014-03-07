#include "WebCrawlerNode.h"

namespace Athena{
    namespace Artemis{
        WebCrawlerNode(){}
        WebCrawlerNode(string ip, int port, int state = AVAILABLE ){
            this->ip=ip; this->port=port; this->state=state;
        }

        string setIp(string i){ ip=i; }
        int setPort( int p){ port=p; }
        int setState( int s ){ state=s; }

        string getIp(){ return ip; }
        int getPort(){ return port; }
        int getState(){ return state; }

        bool isAvailable(){ return (state==AVAILABLE); }

    }


}
