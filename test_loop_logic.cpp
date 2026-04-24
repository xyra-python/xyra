#include "xyra/uWebSockets/src/Loop.h"
#include <iostream>

using namespace uWS;

int main() {
    Loop *loop = Loop::get();

    int key1 = 1, key2 = 2, key3 = 3;

    loop->addPreHandler(&key1, [&key2](Loop *l) {
        std::cout << "preHandler 1\n";
        l->removePreHandler(&key2);
    });

    loop->addPreHandler(&key2, [](Loop *l) {
        std::cout << "preHandler 2\n";
    });

    loop->addPreHandler(&key3, [](Loop *l) {
        std::cout << "preHandler 3\n";
    });

    // Manually trigger preCb to test iterator invalidation behavior
    auto us_loop = (us_loop_t *) loop;

    // We can't directly call preCb because it is private, but wait, preCb is passed to uSockets.
    // Instead of messing with C structure, I will just replicate preCb logic:
    LoopData *loopData = (LoopData *) us_loop_ext(us_loop);

    std::cout << "Calling using safe iteration method:\n";
    for (auto it = loopData->preHandlers.begin(); it != loopData->preHandlers.end(); ) {
        if (it->second) {
            it->second(loop);
        }

        if (!it->second) {
            it = loopData->preHandlers.erase(it);
        } else {
            ++it;
        }
    }

    return 0;
}
