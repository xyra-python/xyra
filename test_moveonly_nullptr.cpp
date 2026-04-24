#include "xyra/uWebSockets/src/MoveOnlyFunction.h"
#include <iostream>

using namespace uWS;

int main() {
    MoveOnlyFunction<void()> f = [](){ std::cout << "Hi\n"; };
    if (f) {
        f();
    }
    f = nullptr;
    if (!f) {
        std::cout << "Nullptr assignment works\n";
    }
}
