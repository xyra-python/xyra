#include <iostream>
#include <map>
#include <vector>
#include <functional>

int main() {
    std::map<int, std::function<void()>> m;

    m[1] = [&]() { std::cout << "Running 1\n"; m.erase(2); };
    m[2] = [&]() { std::cout << "Running 2\n"; };
    m[3] = [&]() { std::cout << "Running 3\n"; };

    std::vector<int> keys;
    for (auto& p : m) {
        keys.push_back(p.first);
    }

    for (auto key : keys) {
        auto it = m.find(key);
        if (it != m.end()) {
            it->second();
        }
    }

    std::cout << "Size: " << m.size() << "\n";
}
