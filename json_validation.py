from typing import Type, Union, Optional, List, Dict, Literal    

class Scheme:
    def __init__(self, schema: dict):
        self.schema = schema
        
    def __str__(self):
        return f'Schema: {str(self.schema)}'

class Constraint:
    def __init__(self, constraint_type: Type, operator: str, value):
        self.constraint_type = constraint_type
        self.operator = operator
        self.value = value

    def is_satisfied(self, value):
        if not isinstance(value, self.constraint_type):
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



def satisfies(value, form, strict=False) -> bool:
    if isinstance(form, Type):
        return isinstance(value, form)
    if isinstance(form, Constraint):
        print(form, value)
        return form.is_satisfied(value)
    if hasattr(form, "__origin__"):
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
        elif form.__origin__ == dict:
            key_type, value_type = form.__args__
            if not isinstance(value, dict):
                return False
            for k, v in value.items():
                if not satisfies(k, key_type):
                    return False
                if not satisfies(v, value_type):
                    return False
            return True
        elif form.__origin__ == Literal:
            return value in form.__args__
    elif isinstance(form, Scheme):
        return validate(value, form.schema, strict=strict) is not None
    else:
        raise TypeError("Unsupported type form")


def validate(instance: dict, form: dict, strict: bool) -> dict:
    if not isinstance(instance, dict):
        raise TypeError("Instance must be a dictionary")

    validated_instance = {}
    
    # Validate each field in the schema
    for key, schema_val in form.items():
        if 'type' not in schema_val:
            # Ignore non-type keys (like functions or literals)
            continue

        field_type = schema_val['type']
        default = schema_val.get('default')

        if key in instance:
            if not satisfies(instance[key], field_type, strict=strict):
                raise TypeError(f"Field '{key}' does not satisfy type {field_type}")
            validated_instance[key] = instance[key]
        else:
            if default is not None:
                validated_instance[key] = default

    # Check for extra fields in the instance if strict mode is on
    if strict:
        for key in instance.keys():
            if key not in form:
                raise ValueError(f"Field '{key}' is not in the scheme")

    return validated_instance

if __name__ == '__main__':


    annotation_schema = {
        'text': {'type': str, 'default': ''},
        'xy': {'type': list, 'default': [0, 0]},
        'xytext': {'type': list, 'default': None},
        'arrowprops': {
            'type': dict,
            'default': {
                'facecolor': 'black',
                'arrowstyle': '->',
            }
        }
    }

    # Gemeinsame Optionen für alle Plots
    common_options = {
        'legend': {'type': bool, 'default': False},
        'xlim': {'type': Optional[List[int]], 'default': None},
        'ylim': {'type': Optional[List[int]], 'default': None},
        'xticks': {'type': Optional[List[int]], 'default': None},
        'yticks': {'type': Optional[List[int]], 'default': None},
        'grid': {'type': bool, 'default': False},
        'annotations': {'type': list, 'default': []},
        'label': {'type': str, 'default': False}
    }

    # Dictionary für die Spezifikationen der Plot-Typen
    plot_specifications = {
        'plot': {
            **common_options,
            'plotter': lambda axe: getattr(axe, 'plot'),
            'options': {
                'color': {'type': Optional[str], 'default': 'black'},
                'linestyle': {'type': Optional[str], 'default': '-'},
                'marker': {'type': Optional[str], 'default': 'o'}
            },
            'data': {
                'x': {'type': list, 'default': []},
                'y': {'type': list, 'default': []}
            },
            'annotation':  {'type': Scheme(annotation_schema), 'default': {}}
        },
        'scatter': {
            **common_options,
            'plotter': lambda axe: getattr(axe, 'scatter'),
            'options': {
                's': {'type': Optional[Union[list, float]], 'default': 20},
                'c': {'type': Optional[Union[list, str]], 'default': 'blue'},
                'marker': {'type': Optional[str], 'default': 'o'},
                'cmap': {'type': Optional[dict], 'default': None},
                'alpha': {'type': Optional[float], 'default': 1.0},
                'linewidths': {'type': Optional[float], 'default': 1.0}
            },
            'data': {
                'x': {'type': list, 'default': []},
                'y': {'type': list, 'default': []}
            }
        },
        'bar': {
            **common_options,
            'plotter': lambda axe: getattr(axe, 'bar'),
            'options': {
                'width': {'type': Optional[float], 'default': 0.8},
                'bottom': {'type': Optional[list], 'default': None},
                'align': {'type': Optional[str], 'default': 'center'},
                'color': {'type': Optional[Union[list, str]], 'default': 'blue'},
                'edgecolor': {'type': Optional[Union[list, str]], 'default': 'black'},
                'linewidth': {'type': Optional[float], 'default': 1.0},
                'tick_label': {'type': Optional[list], 'default': None}
            },
            'data': {
                'x': {'type': list, 'default': []},
                'height': {'type': list, 'default': []}
            }
        }
    }
    

    def test_constraint_success():
        instance = {
            'legend': True,
            'xlim': [0, 10],
            'xlim_length': [1,2],
            'annotation': {
                'text': 'Example',
                'xy': [1, 2],
            }
        }
    
        schema = {
            'legend': {'type': bool, 'default': False},
            'xlim': {'type': Optional[List[int]], 'default': None},
            'annotation': {'type': Scheme(annotation_schema), 'default': {}},
            'xlim_length': {'type': Constraint(list, '>=', 2), 'default': None}  # Expect xlim to have at least 2 elements
        }
    
        validated = validate(instance, schema, strict=False)
        print("Validated (success with constraint):", validated)
    
    def test_constraint_failure():
        instance = {
            'legend': True,
            'xlim': [0],  # This should fail the '>= 2' constraint
            'xlim_length': "",
            'annotation': {
                'text': 'Example',
                'xy': [1, 2]
            }
        }
    
        schema = {
            'legend': {'type': bool, 'default': False},
            'xlim': {'type': Optional[List[int]], 'default': None},
            'annotation': {'type': Scheme(annotation_schema), 'default': {}},
            'xlim_length': {'type': Union[Constraint(list, '>', 10), str], 'default': None}  # Expect xlim to have at least 2 elements
        }
    
        try:
            validated = validate(instance, schema, strict=True)
            print(validated)
        except TypeError as e:
            print("Validation error (failure with constraint):", e)
    
    test_constraint_success()
    test_constraint_failure()
    
