#include <iostream>
#include <map>
#include <functional>

int main() {
    std::map<int, std::function<void()>> m;

    m[1] = [&]() { std::cout << "Running 1\n"; m[2] = nullptr; };
    m[2] = [&]() { std::cout << "Running 2\n"; };
    m[3] = [&]() { std::cout << "Running 3\n"; m[1] = nullptr; };

    for (int i = 0; i < 2; ++i) {
        std::cout << "Iteration " << i << ":\n";
        for (auto it = m.begin(); it != m.end(); ) {
            if (!it->second) {
                it = m.erase(it);
            } else {
                // We must be careful: what if `it->second()` sets the *current* element to nullptr?
                // It won't be erased in this pass, but it will be skipped. Wait, the handler is already invoked.
                // What if it erases the *current* element? Then `++it` is still valid!
                // Wait, if it->second() changes `it->second` to nullptr, `it` is still a valid iterator pointing to the current element.
                // Then we do `++it`, which correctly advances to the next element.
                auto &handler = it->second;
                handler();
                ++it;
            }
        }
        std::cout << "Map size: " << m.size() << "\n";
    }
}
