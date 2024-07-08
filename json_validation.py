from typing import Type, Union, Optional, List, Dict, Literal    

class Scheme(type):
    '''
    Der Scheme type erlaubt es in einem definierten JSON Schema weitere JSON Schemata
    als Typ eines attributs festzulegen
    '''
    def __init__(self, schema: dict):
        self.schema = schema
        
    def __str__(self):
        return f'Schema: {str(self.schema)}'
    
    def __new__(cls,*args, **kwargs):
        klass = super().__new__(cls, "Scheme", (), {})
        return klass

class Constraint(type):
    '''
    Der Contraint type erlaubt es in Typdeklerationen die Werte die typen einnehmen können
    einzuschränken
    '''
    def __init__(self, constraint_type: Type, operator: str, value):
        self.constraint_type = constraint_type
        self.operator = operator
        self.value = value

    def is_satisfied(self, value):
        if not satisfies(value, self.constraint_type):
            return False
        # Check if the type is iterable
        is_iterable =  hasattr(value,'__len__')

        # Determine what to compare: length for iterables or value directly
        to_compare = len(value) if is_iterable else value

        if self.operator == '<':
            return to_compare < self.value
        elif self.operator == '<=':
            return to_compare <= self.value
        elif self.operator == '>':
            return to_compare > self.value
        elif self.operator == '>=':
            return to_compare >= self.value
        elif self.operator == '==':
            return to_compare == self.value
        elif self.operator == '!=':
            return to_compare != self.value
        else:
            return False
        
    def __str__(self):
        return f'Constraint: type={self.constraint_type} op={self.operator} value={self.value}'
    
    def __new__(cls,*args, **kwargs):
        klass = super().__new__(cls, "Constraint", (), {})
        return klass



def satisfies(value, form, strict=False) -> bool:
    '''
    Die satisfies funktion erlaubt es 
    '''
    if isinstance(form, Type) and not isinstance(form, (Constraint, Scheme)):
        return isinstance(value, form)
    if isinstance(form, Constraint):
        return form.is_satisfied(value)
    if hasattr(form, "__origin__"):
        if form.__origin__ == Union:
            types = form.__args__
            return any(satisfies(value, t, strict=strict) for t in types)
        elif form.__origin__ == list:
            inner_type = form.__args__[0]
            if isinstance(value, list):
                return all(satisfies(v, inner_type, strict=strict) for v in value)
            else:
                return False
        elif form.__origin__ == Optional:
            inner_type = form.__args__[0]
            return value is None or satisfies(value, inner_type)
        elif form.__origin__ == dict:
            key_type, value_type = form.__args__
            if not isinstance(value, dict):
                return False
            for k, v in value.items():
                if not satisfies(k, key_type, strict=strict):
                    return False
                if not satisfies(v, value_type, strict=strict):
                    return False
            return True
        elif form.__origin__ == Literal:
            return value in form.__args__
    elif isinstance(form, Scheme):
        if value is None:
            return False
        try:
            res = validate(value, form.schema, strict=strict) 
            value.update(res)
        except:
            return False
        return True
    else:
        raise TypeError("Unsupported type form")


def validate(instance: dict, form: dict, strict: bool) -> dict:
    if not isinstance(instance, dict):
        return False

    validated_instance = {}
    

    for key, schema_val in form.items():
        if not isinstance(schema_val, dict) or 'type' not in schema_val:
            continue
        
        value = instance.get(key)
        field_type = schema_val['type']
        default = schema_val.get('default')

        if key in instance or strict:
            if not satisfies(instance.get(key), field_type, strict=strict):
                raise TypeError(f"Field '{key}' does not satisfy type {field_type}")
            if value != None:
                validated_instance[key] = instance[key]

        if key not in instance and default is not None:
            validated_instance[key] = default

    # Check for extra fields in the instance if strict mode is on
    if strict:
        for key in instance.keys():
            if key not in form:
                raise ValueError(f"Field '{key}' is not in the scheme")

    return validated_instance

if __name__ == '__main__':
    #print(Constraint(int, '==', 1).is_satisfied(1))
    scheme = {
        'lol': {'type': Union[str, bool], 'default': None},
        'lel' : {'type':Optional[str], 'default': 'haha'}
    }

    form = {
            'test' : {'type': Union[Constraint(Union[int,float], '==', 1), bool, Literal['a','b']], 'default': "test"},
            'tesat': {'type': Scheme(scheme), 'default': 'oo'}
            }


    lol = validate({'test': "a", 'tesat': {'lol':True}}, form, strict = True)
    print(lol)