print(type(KeyError("Something to write here")).__name__)

obj = TypeError(["something in array"])
print(type(obj.args), obj.args)