#include <iostream>
#include <map>
#include <functional>

int main() {
    std::map<int, std::function<void()>> preHandlers;

    auto add = [&](int key, std::function<void()> f) {
        auto it = preHandlers.find(key);
        if (it != preHandlers.end()) {
            it->second = std::move(f);
        } else {
            preHandlers.emplace(key, std::move(f));
        }
    };

    auto remove = [&](int key) {
        auto it = preHandlers.find(key);
        if (it != preHandlers.end()) {
            it->second = nullptr;
        }
    };

    add(1, [&]() { std::cout << "Running 1\n"; remove(2); });
    add(2, [&]() { std::cout << "Running 2\n"; });
    add(3, [&]() { std::cout << "Running 3\n"; remove(1); });

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

    std::cout << "Size: " << preHandlers.size() << "\n";
    for (auto& p : preHandlers) std::cout << "Remains: " << p.first << "\n";
}
