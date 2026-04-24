#include "xyra/uWebSockets/src/MoveOnlyFunction.h"
#include <iostream>
#include <map>

using namespace uWS;

int main() {
    std::map<int, MoveOnlyFunction<void()>> handlers;

    handlers.emplace(1, []() { std::cout << "1\n"; });

    for (auto it = handlers.begin(); it != handlers.end(); ) {
        if (!it->second) {
            it = handlers.erase(it);
        } else {
            it->second();
            ++it;
        }
    }

    // Removing a handler
    handlers[1] = nullptr;

    for (auto it = handlers.begin(); it != handlers.end(); ) {
        if (!it->second) {
            it = handlers.erase(it);
        } else {
            it->second();
            ++it;
        }
    }

    std::cout << "Size: " << handlers.size() << "\n";
}
