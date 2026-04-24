#include <iostream>
#include <map>
#include <functional>

int main() {
    std::map<int, std::function<void()>> m;
    bool isIterating = false;

    // Simulate add/remove and iterating

    m[1] = [&]() {
        std::cout << "Running 1\n";
        // remove 2
        if (isIterating) {
            auto it = m.find(2);
            if (it != m.end()) {
                it->second = nullptr;
            }
        } else {
            m.erase(2);
        }
    };
    m[2] = [&]() { std::cout << "Running 2\n"; };
    m[3] = [&]() { std::cout << "Running 3\n"; };

    // Iterate
    isIterating = true;
    for (auto it = m.begin(); it != m.end(); ) {
        if (it->second) {
            it->second();
        }

        if (!it->second) {
            it = m.erase(it);
        } else {
            ++it;
        }
    }
    isIterating = false;

    // cleanup
    for (auto it = m.begin(); it != m.end(); ) {
        if (!it->second) {
            it = m.erase(it);
        } else {
            ++it;
        }
    }
}
