#version 330 core
#define KERNEL_SIZE 20

layout (location = 0) out vec4 fragColor;

in vec2 uvs;
in vec2 screen_res;

uniform sampler2D tex;
uniform float weight[KERNEL_SIZE] = float[] (
    0.0797,	0.0781,	0.0736,	0.0666,	0.0579,	0.0484,	0.0389,	0.0300,	0.0222,	0.0158,	0.0109,	0.0071,	0.0045,	0.0027,	0.0016,	0.0009,	0.0005,	0.0003,	0.0001,	0.0001
);

void main() {
    vec2 st = gl_FragCoord.xy/screen_res;

    vec2 tex_offset = 2.0 / textureSize(tex, 0);
    vec4 color = vec4(st.x, 0.0, st.y, 1.0) * vec4(texture(tex, uvs).rgba) * weight[0];
    // horizontal
    for (int i = 1; i < KERNEL_SIZE; i++) {
        color += vec4(texture(tex, uvs + vec2(tex_offset.x * i, 0.0)).rgba) * weight[i];
        color += vec4(texture(tex, uvs - vec2(tex_offset.x * i, 0.0)).rgba) * weight[i];
    }
    // vertical
    for (int i = 1; i < KERNEL_SIZE; i++) {
        color += vec4(texture(tex, uvs + vec2(0.0, tex_offset.y * i)).rgba) * weight[i];
        color += vec4(texture(tex, uvs - vec2(0.0, tex_offset.y * i)).rgba) * weight[i];
    }

    fragColor = vec4(vec3(1.0,1.0,1.0), color.r + color.g + color.b);
}