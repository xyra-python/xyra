#include <iostream>
#include <map>
#include <functional>

int main() {
    std::map<int, std::function<void()>> m;

    m[1] = [&]() { std::cout << "1\n"; m[2] = nullptr; };
    m[2] = [&]() { std::cout << "2\n"; };
    m[3] = [&]() { std::cout << "3\n"; m[1] = nullptr; };

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

    std::cout << "Size after: " << m.size() << "\n";
    for(auto& p : m) std::cout << "Remains: " << p.first << "\n";
}
