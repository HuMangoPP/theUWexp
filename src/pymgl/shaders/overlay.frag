#version 330 core

layout (location = 0) out vec4 fragColor;

in vec2 uvs;
in vec2 screen_res;

uniform sampler2D tex;

void main() {
    vec2 st = gl_FragCoord.xy/screen_res;
    vec4 color = vec4(texture(tex, uvs).rgb, 1.0);
    if (color.r == 0 && color.g == 0 && color.b == 0) {
        fragColor = vec4(color.rgb, 0.0);
    } else {
        fragColor = vec4(color.rgb, 1.0);
    }
}