from aiohttp import web
from urllib import parse


# ---------- Simple shunting yard algorithm implementation ---------------
import operator as op
import re


class Expression:
    op_mapping = {
                  '+':  op.add,
                  '-':  op.sub,
                  '*':  op.mul,
                  '/':  op.truediv,
                  '**': op.pow,
                }
    op_precedence = {
                '+':   0,
                '-':   0,
                '*':   1,
                '/':   1,
                '**':  1}   
    num_pat = r'(?:\d+|\d\.\d+)'
    op_pat = r'(?:\(|\)|/|\*\*|\*|\+|\-)'

    def __init__(self, expression):
        self.expression = expression
        self._op_stack = list()
        self._val_stack = list()
        self._parens = list()
        self._tokens = None

    def get_precedence(self, op):
        res = self.op_precedence.get(op, None) 
        if res is not None:
            return res
        else:
            raise Exception("Unknown operator {}.".format(op))

    @staticmethod
    def to_numeric(val):
        try:
            res = float(val)
        except ValueError:
            raise
        return res

    async def apply_and_push(self, op=None):
        if op:
            c_op = op
        else:
            c_op = self._op_stack.pop() if self._op_stack else None
        if c_op is not None:
            right = self.to_numeric(self._val_stack.pop())
            left = self.to_numeric(self._val_stack.pop())
            self._val_stack.append(self.op_mapping.get(c_op)(left, right))
        return c_op

    async def evaluate(self):
        """Shunting  yard algorithm implementation"""

        #    I cannot implement algorithm now...
        if self._tokens is None:
            self._tokens = self.tokenizer()

        for token in self._tokens:
            if re.match(self.num_pat, token):
                self._val_stack.append(token)

            elif token == '(':
                self._op_stack.append(token)
            elif token == ')':
                c_op = self._op_stack.pop() if self._op_stack else None
                while c_op is not None and c_op != '(':
                    await self.apply_and_push(op=c_op)
                    c_op = self._op_stack.pop() if self._op_stack else None
            else:
                top_op = self._op_stack[-1] if self._op_stack else None
                while top_op is not None and top_op not in "()" and\
                    self.get_precedence(top_op) >= self.get_precedence(token):
                    top_op = await self.apply_and_push()
                self._op_stack.append(token)

        top_op = self._op_stack[-1] if self._op_stack else None
        while top_op is not None:
            top_op = await self.apply_and_push()
        return self._val_stack.pop()

    def tokenizer(self):
        any_pat = re.compile('(' + '|'.join([self.op_pat,
                                             self.num_pat]) + ')')
        tokens = any_pat.findall(self.expression)
        return tokens
# ------------------------------------------------------------------------



async def evaluate_expression(request):
    parsed = parse.parse_qs(request.query_string).get('expression', None)
    data = "Null or invalid expression"
    if parsed is not None:
        expression = parsed[0]
        try:
            data = await Expression(expression).evaluate()
        except:
            pass
    result = {'answer': data}
    return web.json_response(result)


app = web.Application()
app.add_routes([web.get('/', evaluate_expression)])
web.run_app(app)
