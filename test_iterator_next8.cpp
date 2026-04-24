#include <iostream>
#include <map>
#include <functional>

int main() {
    std::map<int, std::function<void()>> m;
    bool is_iterating = false;

    m[1] = [&]() {
        std::cout << "Running 1\n";
        m.erase(2);
    };
    m[2] = [&]() { std::cout << "Running 2\n"; };
    m[3] = [&]() { std::cout << "Running 3\n"; };

    is_iterating = true;
    for (auto it = m.begin(); it != m.end(); ) {
        // If we want to allow removePreHandler to just queue deletion or we can safely iterate
        // The safest way is to keep a flag 'isIterating' or just iterate over a copy of iterators or something?
        // Wait, std::map is stable, erase invalidates ONLY the erased iterator.

        // If we iterate over a copy of the *keys* ?
        // We can't copy handlers since they are MoveOnlyFunction!
    }
}
