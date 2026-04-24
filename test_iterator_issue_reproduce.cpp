#include "xyra/uWebSockets/src/Loop.h"
#include <iostream>

using namespace uWS;

int main() {
    Loop *loop = Loop::get();

    int key1 = 1, key2 = 2;

    loop->addPreHandler(&key1, [&key2](Loop *l) {
        std::cout << "preHandler 1\n";
        l->removePreHandler(&key2);
    });

    loop->addPreHandler(&key2, [](Loop *l) {
        std::cout << "preHandler 2\n";
    });

    // We can't directly trigger preCb as it is private and not exposed via API
    // We would need to integrate with uSockets loop
}
