#version 330 core
#define KERNEL_SIZE 20

layout (location = 0) out vec4 fragColor;

in vec2 uvs;
in vec2 screen_res;

uniform sampler2D tex;
uniform float weights[KERNEL_SIZE] = float[] (
    0.0797,	0.0781,	0.0736,	0.0666,	0.0579,	0.0484,	0.0389,	0.0300,	0.0222,	0.0158,	0.0109,	0.0071,	0.0045,	0.0027,	0.0016,	0.0009,	0.0005,	0.0003,	0.0001,	0.0001
);

void main() {
    vec2 st = gl_FragCoord.xy/screen_res;

    vec2 tex_offset = 2. / textureSize(tex, 0);
    vec3 color = vec3(texture(tex, uvs).rgb);
    float alpha = 0.;
    if (color != vec3(0)) {
        alpha += weights[0];
    }

    // horizontal
    for (int i = 1; i < KERNEL_SIZE; i++) {
        vec3 color = vec3(texture(tex, uvs + vec2(tex_offset.x * i, 0.)).rgb);
        if (color != vec3(0)) {
            alpha += weights[i];
        }
        color = vec3(texture(tex, uvs - vec2(tex_offset.x * i, 0.)).rgb);
        if (color != vec3(0)) {
            alpha += weights[i];
        }
    }
    // vertical
    for (int i = 1; i < KERNEL_SIZE; i++) {
        vec3 color = vec3(texture(tex, uvs + vec2(0., tex_offset.y * i)).rgb);
        if (color != vec3(0)) {
            alpha += weights[i];
        }
        color = vec3(texture(tex, uvs - vec2(0., tex_offset.y * i)).rgb);
        if (color != vec3(0)) {
            alpha += weights[i];
        }
    }

    fragColor = vec4(1., 1., 1., alpha);
}