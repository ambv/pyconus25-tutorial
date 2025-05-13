"""udataclasses by Diony Rosa packaged in a single file."""

VERSION = "0073db4bfd46b8651c3378345bdaa00f707fcb08"
FIELDS_NAME = "__dataclass_fields__"
FACTORY_SENTINEL = object()
class MissingType:
    """Singleton type for MISSING value."""

    def __repr__(self) -> str:
        return "MISSING"

    def __eq__(self, other: object) -> bool:
        return other is self

MISSING = MissingType()
Any = object  # it doesn't matter for MicroPython

class FrozenInstanceError(AttributeError):
    """Exception raised when attempting to mutate a frozen dataclass instance."""

    pass

def field(
    *,
    default = MISSING,
    default_factory = MISSING,
    init: bool = True,
    repr: bool = True,
    hash: bool | None = None,
    compare: bool = True,
) -> "Field":
    """Function for explicitly declaring a field."""
    return Field(
        default=default,
        default_factory=default_factory,
        init=init,
        repr=repr,
        hash=hash,
        compare=compare,
    )

class Field:
    """
    Internal representation of a field provided by introspection routines.
    Users should not directly instantiate this class.
    """

    name: str
    type: type = object
    default: Any
    default_factory: Any
    init: bool
    repr: bool
    hash: bool | None
    compare: bool

    init_only: bool

    def __init__(
        self,
        name: str = "<UNSET>",
        default: Any = MISSING,
        default_factory = MISSING,
        init: bool = True,
        repr: bool = True,
        hash: bool | None = None,
        compare: bool = True,
        init_only: bool = False,
    ) -> None:
        self.name = name
        self.default = default
        self.default_factory = default_factory
        self.init = init
        self.repr = repr
        self.hash = hash
        self.compare = compare
        self.init_only = init_only

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Field):
            return self.name == other.name
        return False

    def __repr__(self) -> str:
        return f"Field({self.name!r}, {self.default!r})"

    @property
    def _name(self) -> str:
        return f"_{self.name}"

    @property
    def default_value_name(self) -> str:
        """Name to use for storing the default value as a global."""
        return f"__dataclass_default_{self.name}"

    @property
    def contributes_to_hash(self) -> bool:
        """True if this field should contribute to generated __hash__() method."""
        if self.hash is None:
            return self.compare
        return self.hash

ignored_types = {classmethod, staticmethod, property}

class TransformSpec:
    init: bool
    post_init: bool
    repr: bool
    eq: bool
    order: bool
    frozen: bool
    hash: bool | None
    """Tri-state value for adding a __hash__ method.

    If True, add a __hash__ method.
    If False, don't add a __hash__ method.
    If None, set __hash__ to None
    """

    fields: list[Field]
    """Fields sorted alphabetically by name."""

    def __init__(
        self,
        cls: type,
        *,
        init: bool = False,
        repr: bool = False,
        eq: bool = False,
        order: bool = False,
        unsafe_hash: bool = False,
        frozen: bool = False,
    ) -> None:
        self.init = init and ("__init__" not in cls.__dict__)
        self.post_init = "__post_init__" in cls.__dict__
        self.repr = repr and ("__repr__" not in cls.__dict__)
        self.eq = eq
        self.order = order
        self.frozen = frozen

        self.hash = False
        if eq:
            if frozen:
                self.hash = True
            else:
                self.hash = None
        if unsafe_hash:
            self.hash = True

        fields: dict[str, Field] = {}
        # Propagate any existing fields from base class.
        fields.update(getattr(cls, FIELDS_NAME, {}))

        for name, value in cls.__dict__.items():
            field: Field
            if isinstance(value, Field):
                field = value
                field.name = name
            else:
                # Convert implicit field to an explicit one.
                if callable(value) or name.startswith("__"):
                    # Ignore methods and dunder attributes
                    continue
                if type(value) in ignored_types:
                    continue
                field = Field(name, value)

            fields[name] = field
        self.fields = sorted(fields.values(), key=lambda f: f.name)

def _init(fields: list[Field], post_init: bool = False) -> str:
    """Generates the __init__ method."""
    args: list[str] = []
    for field in fields:
        if not field.init:
            continue
        arg = field.name
        if field.default is not MISSING:
            arg += f"={field.default_value_name}"
        if field.default_factory is not MISSING:
            arg += "=FACTORY_SENTINEL"
        args.append(arg)

    # Force all arguments to be keyword-only. Positional arguments are confusing
    # in our use case because we don't preserve the user's field ordering.
    if args:
        args.insert(0, "*")

    body = [line for f in fields if (line := init_initialize_field(f))]

    if post_init:
        body.append("self.__post_init__()")

    return method(
        name="__init__",
        non_self_args=args,
        body=body or "pass",
    )

def init_initialize_field(f: Field) -> str:
    """__init__() body line to assign field an initial value.

    Empty string if no initializion is needed.
    """
    left = f"self.{f._name}"
    if f.init:
        value = f.name
        if f.default_factory is not MISSING:
            value = f"{f.default_value_name}() if {f.name} is FACTORY_SENTINEL else {f.name}"
        return f"{left} = {value}"
    # Initialize init=False field
    if f.default is not MISSING:
        return f"{left} = {f.default_value_name}"
    if f.default_factory is not MISSING:
        return f"{left} = {f.default_value_name}()"
    return ""

def _getter(field: Field) -> str:
    """Generates a field getter."""
    return method(
        decorator="@property",
        name=field.name,
        body=f"return self.{field._name}",
    )

def _setter(field: Field, frozen: bool = False) -> str:
    """Generates a field setter."""
    return method(
        decorator=f"@{field.name}.setter",
        name=field.name,
        non_self_args=["value"],
        body=(
            f"raise FrozenInstanceError('{field.name}')"
            if frozen
            else f"self.{field._name} = value"
        ),
    )

def _deleter(field: Field, frozen: bool = False) -> str:
    """Generates a field deleter."""
    return method(
        decorator=f"@{field.name}.deleter",
        name=field.name,
        body=(
            f"raise FrozenInstanceError('{field.name}')"
            if frozen
            else f"del self.{field._name}"
        ),
    )

def _repr(fields: list[Field]) -> str:
    """Generates the __repr__ method."""
    return method(
        name="__repr__",
        body=(
            "return f'{self.__class__.__name__}("
            + ", ".join(f"{f.name}={{self.{f._name}!r}}" for f in fields if f.repr)
            + ")'"
        ),
    )

def _eq(fields: list[Field]) -> str:
    return compare("__eq__", "==", fields)

def _lt(fields: list[Field]) -> str:
    return compare("__lt__", "<", fields)

def _le(fields: list[Field]) -> str:
    return compare("__le__", "<=", fields)

def _gt(fields: list[Field]) -> str:
    return compare("__gt__", ">", fields)

def _ge(fields: list[Field]) -> str:
    return compare("__ge__", ">=", fields)

def _hash(fields: list[Field]) -> str:
    hash_fields = [f for f in fields if f.contributes_to_hash]
    return method(
        name="__hash__", body=f"return hash({tuple_str('self', hash_fields)})"
    )

def method(
    *,
    name: str,
    body: str | list[str],
    decorator: str | None = None,
    non_self_args: list[str] = [],
) -> str:
    """Generates code for a Python method."""
    lines: list[str] = []
    if decorator is not None:
        lines.append(decorator)
    lines.append(f"def {name}({', '.join(['self'] + non_self_args)}):")
    if isinstance(body, str):
        body = [body]
    indent = " " * 4
    for line in body:
        lines.append(indent + line)
    return "\n".join(lines)

def tuple_str(object_name: str, fields: list[Field]) -> str:
    """An expressing that represents a dataclass instance as a tuple of its fields."""
    parts = (f"{object_name}._{f.name}," for f in fields)
    return f"({' '.join(parts)})"

def compare(name: str, operator: str, fields: list[Field]) -> str:
    """Generates a comparison operator method."""
    compare_fields = [f for f in fields if f.compare]
    left = tuple_str("self", compare_fields)
    right = tuple_str("other", compare_fields)
    return method(
        name=name,
        non_self_args=["other"],
        body=f"return {left} {operator} {right}",
    )

def is_dataclass(obj: object) -> bool:
    """Check if an object or class is a dataclass."""
    cls = obj if isinstance(obj, type) else type(obj)
    return hasattr(cls, FIELDS_NAME)

def fields(obj: object) -> tuple[Field, ...]:
    """Retrieve all the Fields of an object or class."""
    cls = obj if isinstance(obj, type) else type(obj)
    return tuple(getattr(cls, FIELDS_NAME).values())

def replace(obj: Any, **changes: Any) -> Any:
    """Create a new object with the specified fields replaced."""
    fields = getattr(obj, FIELDS_NAME)
    init_args = {f.name: getattr(obj, f.name) for f in fields.values() if f.init}
    for name, new_value in changes.items():
        field = fields.get(name)
        if not field:
            raise TypeError(f"Unknown field: {name}")
        if not field.init:
            raise ValueError(f"Cannot replace field defined with init=False: {name}")
        init_args[name] = new_value
    return (type(obj))(**init_args)

def dataclass(
    cls: type | None = None, **kwargs: Any
) -> Any:
    """Decorator to transform a normal class into a dataclass."""

    def wrapper(cls: type) -> type:
        return _dataclass(cls, **kwargs)

    if cls is None:
        # Decorator called with no arguments
        return wrapper

    # Decorator called with arguments
    return wrapper(cls)

def _dataclass(
    cls: type,
    *,
    init: bool = True,
    repr: bool = True,
    eq: bool = True,
    order: bool = False,
    unsafe_hash: bool = False,
    frozen: bool = False,
) -> type:
    transform = TransformSpec(
        cls,
        init=init,
        repr=repr,
        eq=eq,
        order=order,
        unsafe_hash=unsafe_hash,
        frozen=frozen,
    )

    for name, value in make_methods(transform).items():
        setattr(cls, name, value)

    # Store fields metadata
    setattr(cls, FIELDS_NAME, {f.name: f for f in transform.fields})
    return cls

def make_global_bindings(transform: TransformSpec) -> dict[str, Any]:
    bindings: dict[str, Any] = {
        "FrozenInstanceError": FrozenInstanceError,
        "FACTORY_SENTINEL": FACTORY_SENTINEL,
    }
    for field in transform.fields:
        if field.default is not MISSING:
            bindings[field.default_value_name] = field.default
        if field.default_factory is not MISSING:
            bindings[field.default_value_name] = field.default_factory
    return bindings

def make_methods(transform: TransformSpec) -> dict[str, Any]:
    global_bindings = make_global_bindings(transform)
    methods: dict[str, Any] = {}

    def add_method(code: str) -> None:
        exec(code, global_bindings, methods)

    for field in transform.fields:
        add_method(_getter(field))
        add_method(_setter(field, transform.frozen))
        add_method(_deleter(field, transform.frozen))

    if transform.init:
        add_method(_init(transform.fields, post_init=transform.post_init))
    if transform.repr:
        add_method(_repr(transform.fields))
    if transform.eq:
        add_method(_eq(transform.fields))
    if transform.order:
        add_method(_lt(transform.fields))
        add_method(_le(transform.fields))
        add_method(_gt(transform.fields))
        add_method(_ge(transform.fields))

    if transform.hash is None:
        methods["__hash__"] = None
    if transform.hash:
        add_method(_hash(transform.fields))

    return methods
