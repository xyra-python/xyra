#include <iostream>
#include <map>
#include <functional>

int main() {
    std::map<int, std::function<void()>> m;

    m[1] = [&]() { std::cout << "Running 1\n"; m.erase(1); };
    m[2] = [&]() { std::cout << "Running 2\n"; };

    for (auto it = m.begin(); it != m.end(); ) {
        // Here, it->second() calls m.erase(1) which invalidates `it`.
        it->second();
        ++it; // Crash/UB here!
    }

    std::cout << "Size: " << m.size() << "\n";
}
