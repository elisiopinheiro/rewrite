def popper(data: dict, props_to_pop: list[str]):
    for prop in props_to_pop:
        data.pop(prop)
