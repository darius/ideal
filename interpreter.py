"""
Interpreter for IDEAL abstract syntax.
"""

from itertools import count
import operator

from structs import Struct
import linear_constraints as LC
import linear_equations as LE
import drawing

class Environment(Struct('types constrainers drawers frames')):
    def spawn(self, frame):
        return Environment(self.types, self.constrainers, self.drawers,
                           self.frames + (frame,))
    def add_constrainer(self, constrainer):
        self.constrainers.append((constrainer, self))
    def add_drawer(self, drawer):
        self.drawers.append((drawer, self))

def run(defs):
    root_env = Environment({box.name: box for box in defs},
                           [], [], ({},))
    # First we create all the variables...
    root_env.types['main'].make(root_env)

    # ...then create the constraints. We waited because an equation
    # might use forward refs.
    for constrainer, env in root_env.constrainers:
        constrainer.constrain(env)

    drawing.begin()
    for drawer, env in root_env.drawers:
        drawer.draw(env)
    drawing.end()

counter = count(1)

def gensym():
    return 'g#%d' % next(counter)

class Box(Struct('name stmts')):
    def make(self, env):
        for stmt in self.stmts:
            stmt.build(env)

class Decl(Struct('names')):
    def build(self, env):
        for name in self.names:
            lin_exp = LE.LinExp(0, [(LC.Variable(name), 1)])
            env.frames[-1][name] = LC.Number(lin_exp)

class Conn(Struct('points')):
    def build(self, env):
        env.add_drawer(self)
    def draw(self, env):
        points = [p.evaluate(env).get_value() for p in self.points]
        drawing.polyline(map(to_coords, points))

class Text(Struct('justified string where')):
    def build(self, env):
        env.add_drawer(self)
    def draw(self, env):
        at = self.where.evaluate(env).get_value()
        drawing.text(self.string, self.justified or 'center', to_coords(at))

def to_coords(point):
    return point.real, point.imag

class Put(Struct('opt_name box')):
    def build(self, env):
        name = self.opt_name or gensym()  # (The default name's just for debugging.)
        subenv = env.spawn({})
        env.types[self.box.name].make(subenv)
        env.frames[-1][name] = subenv.frames[-1]
        for stmt in self.box.stmts:
            stmt.build(subenv)

class Default(Struct('parts')):
    def build(self, env):
        assert False, "XXX unimplemented"

class Equate(Struct('parts')):
    def build(self, env):
        env.add_constrainer(self)
    def constrain(self, env):
        reduce(LC.equate, (expr.evaluate(env) for expr in self.parts))

class Ref(Struct('name')):
    def evaluate(self, env):
        for frame in reversed(env.frames):
            try:
                return frame[self.name]
            except KeyError:
                pass
        raise KeyError("Unbound name", self.name)

class Of(Struct('ref field')):
    def evaluate(self, env):
        return self.ref.evaluate(env)[self.field]

class Literal(Struct('value')):
    def evaluate(self, env):
        return LC.Number(LE.LinExp(self.value, ()))

class BinaryOp(Struct('arg1 arg2')):
    def evaluate(self, env):
        return self.operate(self.arg1.evaluate(env),
                            self.arg2.evaluate(env))

class Add(BinaryOp): operate = operator.add
class Sub(BinaryOp): operate = operator.sub
class Mul(BinaryOp): operate = operator.mul
class Div(BinaryOp): operate = operator.truediv

def Negate(expr): return Sub(Literal(0j), expr)

class Interpolate(Struct('alpha zero one')):
    def evaluate(self, env):
        alpha = self.alpha.evaluate(env)
        zero = self.zero.evaluate(env)
        one = self.one.evaluate(env)
        return zero + (one - zero) * alpha;
