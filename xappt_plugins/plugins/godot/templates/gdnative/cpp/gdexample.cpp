#include "{CLASS_NAME!l}.h"

using namespace godot;

void {CLASS_NAME}::_register_methods() {
    register_method("_process", &{CLASS_NAME}::_process);
    register_property<{CLASS_NAME}, float>("amplitude", &{CLASS_NAME}::amplitude, 10.0);
    register_property<{CLASS_NAME}, float>("speed", &{CLASS_NAME}::set_speed, &{CLASS_NAME}::get_speed, 1.0);

    register_signal<{CLASS_NAME}>((char *)"position_changed", "node", GODOT_VARIANT_TYPE_OBJECT, "new_pos", GODOT_VARIANT_TYPE_VECTOR2);
}

{CLASS_NAME}::{CLASS_NAME}() {}

{CLASS_NAME}::~{CLASS_NAME}() {}

void {CLASS_NAME}::_init() {
    time_passed = 0.0;
    amplitude = 10.0;
    speed = 1.0;
    time_emit = 0.0;
}

void {CLASS_NAME}::_process(float delta) {
    time_passed += speed * delta;

    Vector2 new_position = Vector2(
        amplitude + (amplitude * sin(time_passed * 2.0)), 
        amplitude + (amplitude * cos(time_passed * 1.5))
    );

    set_position(new_position);

    time_emit += delta;
    if (time_emit > 1.0) {
        emit_signal("position_changed", this, new_position);
        time_emit = 0.0;
    }
}

void {CLASS_NAME}::set_speed(float p_speed) {
    speed = p_speed;
}

float {CLASS_NAME}::get_speed() {
    return speed;
}


