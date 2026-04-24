#include <iostream>
#include <map>
#include <functional>

int main() {
    std::map<int, std::function<void()>> m;

    m[1] = [&]() { std::cout << "Running 1\n"; m.erase(2); };
    m[2] = [&]() { std::cout << "Running 2\n"; };
    m[3] = [&]() { std::cout << "Running 3\n"; };

    for (auto it = m.begin(); it != m.end(); ) {
        // Safe way: advance the iterator before calling the handler
        auto current = it++;
        current->second();
    }

    std::cout << "Size: " << m.size() << "\n";
}
