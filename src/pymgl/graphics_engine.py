import moderngl as mgl
import numpy as np
import pygame as pg
import glm
import os

FOV = 50
NEAR = 0.1
FAR = 100

class GraphicsEngine:
    def __init__(self, ctx: mgl.Context, res: tuple[int, int], path: str):
        """
        The `GraphicsEngine` is a rendering engine designed to render a layer onto the
        pygame window after applying a shader. Currently, the `GraphicsEngine` only supports
        full layer rendering as opposed to object rendering

        The `GraphicsEngine` takes as input:

        * `ctx`: a moderngl context which should be created from pygame during initialization

        * `res`: the screen resolution
        """
        self.ctx = ctx
        self.res = res
        self.path = path

        # shader programs
        self.programs : dict[str, mgl.Program] = {}
        self._load_all_shaders()

        # vertex buffer objects
        self.vbo = self._get_vbo()

        # vertex array objects
        self.vaos : dict[str, mgl.VertexArray] = {}
        self._get_all_vaos()

        self.texture = None

    def _get_program(self, shader_name: str) -> mgl.Program:
        """
        Helper function which will load the fragment shader
        """
        with open(f'{self.path}/pymgl/shaders/default.vert') as file:
            vertex_shader = file.read()
        with open(f'{self.path}/pymgl/shaders/{shader_name}.frag') as file:
            frag_shader = file.read()

        program = self.ctx.program(vertex_shader=vertex_shader, fragment_shader=frag_shader)
        program['res'].write(glm.vec2(self.res[0], self.res[1]))
        m_model = glm.mat4()

        # translate
        pos = (0, 0, 0)
        m_model = glm.translate(m_model, pos)

        # scale
        scale = (1, 1, 1)
        m_model = m_model * glm.scale(scale)

        # write
        program['m_model'].write(m_model)

        return program

    def _load_all_shaders(self):
        """
        Helper function which loads all fragment shaders in the `shaders/` directory
        """
        shaders = os.listdir(f'{self.path}/pymgl/shaders')
        for shader in shaders:
            shader_name = shader.split('.')
            if shader_name[1] == 'frag':
                self.programs[shader_name[0]] = self._get_program(shader_name[0])

    @staticmethod
    def _get_data(
        vertices: list[tuple[float, float]], 
        indices: list[tuple[float, float, float]]
    ) -> np.ndarray[np.float32]:
        """
        Helper function to retrieve the vertex array data from a set of vertices and indices specifying a triangle
        """
        data = [vertices[ind] for triangle in indices for ind in triangle]
        return np.array(data, dtype='f4')

    def _get_vertex_data(self) -> np.ndarray[np.float64]:
        """
        Helper function to retrieve all of the vertex array data
        """
        vertices = [(-1, 1), (1, 1), (1, -1), (-1, -1)]
        tex_vert = [(0, 0), (1, 0), (1, 1), (0, 1)]
        indices = [(0, 1, 2), (0, 2, 3)]

        vertex_data = np.hstack([
            self._get_data(vertices, indices), 
            self._get_data(tex_vert, indices)
        ])
        return np.hstack(vertex_data)

    def _get_vbo(self) -> mgl.Buffer:
        """
        Helper function which will retrieve the context buffer from the vertex data
        """
        vertex_data = self._get_vertex_data()
        vbo = self.ctx.buffer(vertex_data)
        return vbo

    def _get_vao(self, program: mgl.Program) -> mgl.VertexArray:
        """
        Helper function that will get the vertex array object
        """
        return self.ctx.vertex_array(program, [(self.vbo, '2f 2f', 'vertcoord', 'texcoord')])

    def _get_all_vaos(self):
        """
        Helper function that will create a vertex array object for every shader program
        """
        for program_name in self.programs:
            self.vaos[program_name] = self._get_vao(self.programs[program_name])

    def _update_texture(self, surf_size: tuple[int, int], surf: pg.Surface):
        """
        Helper function to update the texture of the quad which will be drawn to the pygame display
        """
        if not self.texture:
            self.texture = self.ctx.texture(size=surf_size, components=4)
            self.texture.repeat_x = False
            self.texture.repeat_y = False
            self.texture.filter = (mgl.NEAREST, mgl.NEAREST)
            self.texture.swizzle = 'BGRA'
        self.texture.write(surf.get_view('1'))
        self.texture.use()
    
    # def write_program_data(self, shader: str, render_data: dict[str, any]):
    #     for key in render_data:
    #         self.programs[shader][key].write(render_data[key])

    # def write_model_data(self, shader: str, rect: pg.Rect):
    #     width, height = self.res
    #     m_model = glm.mat4()

    #     # translate
    #     pos = (rect.centerx/width*2-1, -(rect.centery/height*2-1), 0)
    #     m_model = glm.translate(m_model, pos)

    #     # scale
    #     scale = (rect.width/width, rect.height/height, 1)
    #     m_model = m_model * glm.scale(scale)

    #     # write
    #     self.programs[shader]['m_model'].write(m_model)

    def render(self, surf: pg.Surface, shader: str='default'):
        """
        The render method which will be used to apply the fragment shader to the layer and render it onto the 
        pygame display. Takes as input

        * `surf`, the layer

        * `shader`, the name of the shader to apply
        """
        surf_size = surf.get_size()
        self._update_texture(surf_size, surf)
        self.programs[shader]['tex'] = 0
        # self.write_model_data(shader, rect)
        # self.write_program_data(shader, render_data)
        vao = self.vaos[shader]
        vao.render()

    def destroy(self):
        """
        Call this function on program exit to release all memory associated with the `GraphicsEngine`
        """
        self.texture.release()
        self.vbo.release()
        [program.release() for program in self.programs.values()]