#ifndef {CLASS_NAME!u}_H
#define {CLASS_NAME!u}_H

#include <Godot.hpp>
#include <Sprite.hpp>

namespace godot {

class {CLASS_NAME} : public Sprite {
    GODOT_CLASS({CLASS_NAME}, Sprite)

private:
    float time_passed;
    float amplitude;
    float speed;
    float time_emit;

public:
    static void _register_methods();

    {CLASS_NAME}();
    ~{CLASS_NAME}();

    void _init(); // our initializer called by Godot

    void _process(float delta);
    void set_speed(float p_speed);
    float get_speed();
};

}

#endif

