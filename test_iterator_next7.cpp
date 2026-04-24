#include <iostream>
#include <map>
#include <functional>

int main() {
    std::map<int, std::function<void()>> m;

    m[1] = [&]() { std::cout << "Running 1\n"; m.erase(2); };
    m[2] = [&]() { std::cout << "Running 2\n"; };
    m[3] = [&]() { std::cout << "Running 3\n"; };

    for (auto it = m.begin(); it != m.end(); ) {
        auto next = std::next(it); // get next before calling the function!
        it->second();
        it = next; // if the next one is erased, this next is invalidated!
    }

    std::cout << "Size: " << m.size() << "\n";
}
