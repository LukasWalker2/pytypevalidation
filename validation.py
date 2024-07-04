from typing import Type, Union, Optional, List

def satisfies(value, form) -> bool:
    if isinstance(form, Type):
        return isinstance(value, form)
    elif hasattr(form, "__origin__"):
        if form.__origin__ == Union:
            types = form.__args__
            return any(satisfies(value, t) for t in types)
        elif form.__origin__ == list:
            inner_type = form.__args__[0]
            if isinstance(value, list):
                return all(satisfies(v, inner_type) for v in value)
            else:
                return False
        elif form.__origin__ == Optional:
            inner_type = form.__args__[0]
            return value is None or satisfies(value, inner_type)
    else:
        raise TypeError("Unsupported type form")

print(satisfies(10, Union[int, float]))                                                                                    # True
print(satisfies("test", Optional[int]))                                                                                    # False
print(satisfies(1, Optional[int]))                                                                                         # True
print(satisfies([[1, 2], [3, 4]], List[List[int]]))                                                                        # True
print(satisfies([[1, 2], [3, None]], List[List[Optional[int]]]))                                                           # True
print(satisfies([[1, 2], [3, "test"]], List[List[int]]))                                                                   # False
print(satisfies([[[1, 2], [3, 4]], [[5, 6], [7, 8]]], List[List[List[int]]]))                                              # True
print(satisfies([[[1, 2], [3, None]], [[None, 5], [6, 7]]], List[List[List[Optional[int]]]]))                              # True
print(satisfies([[[1, 2], [3, "test"]], [[True, False], [None, None]]], List[List[List[int]]]))                            # False
print(satisfies([[[1.0, 2], [3, 4.0]], [[5, 6.0], [7.0, 8]]], List[List[List[Union[float, int]]]]))                        # True
print(satisfies([[["test", 2, 1.2], [3, "test"]], [[5, "test"], ["test", 8]]], List[List[List[Union[str, int, float]]]]))  # True
print(satisfies(None, Optional[List[List[int]]]))                                                                          # True
print(satisfies([[1, 2], [3, None]], Optional[List[List[Optional[int]]]]))                                                 # True