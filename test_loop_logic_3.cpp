#include <iostream>
#include <map>
#include <functional>

int main() {
    std::map<void*, std::function<void()>> preHandlers;
    bool isIteratingPreHandlers = false;

    // We can iterate the map using iterators:
    for (auto it = preHandlers.begin(); it != preHandlers.end(); ) {
        if (it->second) {
            it->second();
        }

        if (!it->second) {
            it = preHandlers.erase(it);
        } else {
            ++it;
        }
    }
}
