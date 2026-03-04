import click
from .database import NoteStore
from .utils import  get_db_path
from . import commands

@click.group()
@click.pass_context
def cli(ctx):
    db_path = get_db_path()
    ctx.obj = NoteStore(db_path)

cli.add_command(commands.edit_note)
cli.add_command(commands.create)
cli.add_command(commands.search)
cli.add_command(commands.list_notes)
cli.add_command(commands.delete_note)
cli.add_command(commands.retag)
cli.add_command(commands.rename_note)
cli.add_command(commands.show_notes)

