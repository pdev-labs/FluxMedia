from rich.prompt import Prompt; old_ask = Prompt.ask; Prompt.ask = lambda q, *a, **kw: 'mocked'; print(Prompt.ask('Hello?'))
