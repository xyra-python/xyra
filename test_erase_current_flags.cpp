#include <iostream>
#include <map>
#include <functional>

int main() {
    std::map<int, std::function<void()>> m;
    bool isIterating = false;

    auto removeHandler = [&](int key) {
        if (isIterating) {
            auto it = m.find(key);
            if (it != m.end()) {
                it->second = nullptr;
            }
        } else {
            m.erase(key);
        }
    };

    m[1] = [&]() { std::cout << "Running 1\n"; removeHandler(1); };
    m[2] = [&]() { std::cout << "Running 2\n"; removeHandler(3); };
    m[3] = [&]() { std::cout << "Running 3\n"; };

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
    std::cout << "Size: " << m.size() << "\n";
}
