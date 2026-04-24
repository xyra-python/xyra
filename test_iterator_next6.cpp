#include <iostream>
#include <map>
#include <functional>

int main() {
    // If we queue deletions
    std::map<int, std::function<void()>> m;
    std::map<int, std::function<void()>> current_m;

    m[1] = [&]() { std::cout << "Running 1\n"; m.erase(2); };
    m[2] = [&]() { std::cout << "Running 2\n"; };
    m[3] = [&]() { std::cout << "Running 3\n"; };

    // Copy the map before iterating?
    current_m = m;
    for (auto& p : current_m) {
        if (m.count(p.first)) { // Check if it hasn't been erased from the real map
            p.second();
        }
    }

    std::cout << "Size: " << m.size() << "\n";
}
