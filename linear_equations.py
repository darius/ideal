"""
Solve sparse systems of linear equations.
"""

from __future__ import division

class LinExp(object):
    "A linear expression in some variables."
    def __init__(self, constant, terms):
        self.constant = constant
        self.terms = {var: val for var, val in terms if val != 0}
    def combine(self, c, e2, c2):
        return LinExp(c * self.constant + c2 * e2.constant,
                      ((var, (c * self.coefficient(var)
                              + c2 * e2.coefficient(var)))
                       for var in self.variables() | e2.variables()))
    def scale(self, c):
        return self.combine(c, zero, 0)
    def add(self, e2):
        return self.combine(1, e2, 1)
    def coefficient(self, variable):
        return self.terms.get(variable, 0)
    def variables(self):
        return set(self.terms.iterkeys())
    def a_variable(self):
        return next(self.terms.iterkeys(), None)
    def is_constant(self):
        return not self.terms
    # The remaining methods treat LinExps as equations implicitly ==
    # 0. So one is inconsistent if it's something like 5==0, it
    # defines a variable if it's something like 1*x-3==0 (with just
    # one variable), and so on.
    def is_inconsistent(self):
        return self.is_constant() and self.constant != 0
    def is_tautology(self):
        return self.is_constant() and self.constant == 0
    def defines_var(self):
        vars = self.terms.keys()
        return (vars if len(vars) == 1 and self.coefficient(vars[0]) == 1
                else ())
    def substitute_for(self, var, eq):
        """Return an equivalent equation with var eliminated by
        resolving against eq (which must have a term for var)."""
        # self - (self[var]/eq[var]) * eq
        c = -self.coefficient(var) / eq.coefficient(var)
        return self.combine(1, eq, c)
    def normalize(self):
        """Return an equivalent equation with a variable's coefficient
        rescaled to 1."""
        var = self.a_variable()
        return self.scale(1 / self.coefficient(var))
    def __repr__(self):
        items = sorted(self.terms.items())
        if self.constant:
            items = [('', self.constant)] + items
        if not items: return '(0 = 0)'
        def format((var, c)):
            if var == '': return '%g' % c
            if c == 1:    return '%s' % (var,)
            if c == -1:   return '-%s' % (var,)
            return '%g%s' % (c, var)
        def combiner(pair):      # XXX rename
            f = format(pair)
            return ' - ' + f[1:] if f.startswith('-') else ' + ' + f
        return '(0 = %s%s)' % (format(items[0]),
                               ''.join(map(combiner, items[1:])))

zero = LinExp(0, ())

def solve_equations(eqs):
    """Return a dict mapping variables to values, for those variables
    eqs constrains to a value. An eq is a LinExp implicitly equated to
    0."""
    consistent, eqs = reduce_equations(eqs)
    if not consistent:
        return {}               # or None, or what?
    return {var: -le.constant
            for le in eqs
            for var in le.defines_var()}

def reduce_equations(eqs):
    """Try to reduce eqs to an equivalent system with each variable
    defined by a single equation. The first result is False if the
    eqs are inconsistent. The result may still be underconstrained."""
    for i, eqi in enumerate(eqs):
        var = eqi.a_variable()
        if not var: continue
        for j, eqj in enumerate(eqs):
            if i == j: continue
            eqs[j] = eqj.substitute_for(var, eqi)
            if eqs[j].is_inconsistent():
                return False, eqs
    return True, [eq.normalize() for eq in eqs if not eq.is_tautology()]
