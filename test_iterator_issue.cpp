#include "xyra/uWebSockets/src/Loop.h"
#include <iostream>

using namespace uWS;

int main() {
    Loop *loop = Loop::get();

    int key1 = 1, key2 = 2, key3 = 3;

    loop->addPreHandler(&key1, [&key2](Loop *l) {
        std::cout << "Running preHandler 1" << std::endl;
        l->removePreHandler(&key2); // This causes iterator invalidation if the loop is currently iterating
    });

    loop->addPreHandler(&key2, [](Loop *l) {
        std::cout << "Running preHandler 2" << std::endl;
    });

    loop->addPreHandler(&key3, [](Loop *l) {
        std::cout << "Running preHandler 3" << std::endl;
    });

    loop->run(); // How to just trigger one iteration or test it? We can directly call preCb

    return 0;
}
