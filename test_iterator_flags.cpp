#include <iostream>
#include <map>
#include <functional>

int main() {
    std::map<int, std::function<void()>> handlers;
    bool isIterating = false;

    auto removeHandler = [&](int key) {
        if (isIterating) {
            auto it = handlers.find(key);
            if (it != handlers.end()) {
                it->second = nullptr;
            }
        } else {
            handlers.erase(key);
        }
    };

    handlers[1] = [&]() {
        std::cout << "preHandler 1\n";
        removeHandler(2);
    };

    handlers[2] = [&]() { std::cout << "preHandler 2\n"; };

    handlers[3] = [&]() { std::cout << "preHandler 3\n"; };


    isIterating = true;
    for (auto it = handlers.begin(); it != handlers.end(); ) {
        if (it->second) {
            it->second();
        }

        if (!it->second) {
            it = handlers.erase(it);
        } else {
            ++it;
        }
    }
    isIterating = false;

    std::cout << "Size: " << handlers.size() << "\n";
    for(auto &p : handlers) {
        std::cout << "Remains: " << p.first << "\n";
    }

}
