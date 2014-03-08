#include "WebCrawlerNode.h"

namespace Athena{
    namespace Artemis{

        WebCrawlerNode::WebCrawlerNode(){}
        WebCrawlerNode::WebCrawlerNode(string ip, int port, int state ){
            this->ip=ip; this->port=port; this->state=state;
        }

        string WebCrawlerNode::setIp(string i){ ip=i; }
        int WebCrawlerNode::setPort( int p){ port=p; }
        int WebCrawlerNode::setState( int s ){ state=s; }

        string WebCrawlerNode::getIp(){ return ip; }
        int WebCrawlerNode::getPort(){ return port; }
        int WebCrawlerNode::getState(){ return state; }

        bool WebCrawlerNode::isAvailable(){ return (state==AVAILABLE); }

    }


}
