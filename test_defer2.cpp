#include <iostream>
#include <map>
#include <vector>
#include <functional>

int main() {
    std::map<int, std::function<void()>> m;
    bool isIterating = false;

    m[1] = [&]() {
        std::cout << "Running 1\n";
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
