import click

if not hasattr(click.Choice, "__class_getitem__"):
    click.Choice.__class_getitem__ = classmethod(lambda cls, _item: cls)
