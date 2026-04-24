#include <iostream>
#include <map>
#include <functional>

int main() {
    std::map<int, std::function<void()>> m;

    m[1] = [&]() { std::cout << "Running 1\n"; m.erase(2); };
    m[2] = [&]() { std::cout << "Running 2\n"; };
    m[3] = [&]() { std::cout << "Running 3\n"; };

    // Copy the map to avoid invalidation issues, actually wait: MoveOnlyFunction can't be copied.
    // What if we maintain `isIteratingPostHandlers` / `isIteratingPreHandlers` flags in LoopData?
    // Oh! wait, the loop code says:
    // "Bug: what if you remove a handler while iterating them?"
    // And "Can be solved by queuing deletions or copying the map before iterating." Wait, the map CAN be copied if we just store raw pointers? No, it holds `MoveOnlyFunction`.
    // Wait, the prompt says "Can be solved by queuing deletions or copying the map before iterating." wait! We can't copy MoveOnlyFunction.
    // Wait, wait... what if we queue deletions in LoopData?
}
