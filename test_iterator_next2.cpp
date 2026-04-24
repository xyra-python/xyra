#include <iostream>
#include <map>
#include <functional>

int main() {
    std::map<int, std::function<void()>> m;

    m[1] = [&]() { std::cout << "Running 1\n"; m.erase(2); };
    m[2] = [&]() { std::cout << "Running 2\n"; };

    for (auto it = m.begin(); it != m.end(); ) {
        // We cannot call m.erase(2) during the loop, because if we do,
        // and we haven't reached 2 yet, it's fine for the loop itself since map iterators are stable.
        // Wait, if it->second() calls m.erase(2) and `it` points to 1,
        // after `it->second()`, `it` still points to 1. `++it` will correctly point to end().
        it->second();
        ++it;
    }

    std::cout << "Size: " << m.size() << "\n";
}
