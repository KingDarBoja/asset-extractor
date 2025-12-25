# Core Parsing Logic Memory

## Attribute Inheritance
- **Strict Type Assumption**: The `resolve_inheritance` method in `Attribute` subclasses (in `attributes.py`) strictly assumes that the `default` parameter is an instance of the same subclass.
- **Type Hinting**: Use `t.Self` for the `default` parameter to enforce this assumption.
- **LSP Violation**: This pattern technically violates the Liskov Substitution Principle (LSP) by narrowing the input type of overridden methods.
- **Pyright Suppression**: Always use `# pyright: ignore[reportIncompatibleMethodOverride]` on these methods to suppress static analysis errors, as the project architecture guarantees type compatibility at runtime.
