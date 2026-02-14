import sqlite3
import click
from .database import NoteStore
from .utils import validate_title, slugify, get_db_path, validate_tags, clean_title
from rich.console import Console
from rich.markdown import Markdown
from rich.padding import Padding

console = Console()

@click.group()
@click.pass_context
def cli(ctx):
    db_path = get_db_path()
    ctx.obj = NoteStore(db_path)


@cli.command(name="edit")
@click.argument("name")
@click.pass_context
def edit_note(ctx, name):
    store = ctx.obj
    slug = slugify(name)
    content = store.get_content(slug)

    if content is None:
        click.secho(f"Note {name} not found!", fg="yellow")
        return

    initial_content = str(content) if content else ""
    new_content = click.edit(initial_content, extension='.md', require_save=True)

    if new_content is not None and new_content != content:
        store.update_content(slug, new_content)
        store.export_debug_log()
        click.secho(f"Note {name} with slug:{slug} updated!", fg="green")
    else:
        click.secho(f"No changes in {slug}, nothing saved", fg="yellow")


@cli.command(name="create")
@click.argument("title")
@click.option("--tags", "-t", default=None, help="Tags separated by commas")
@click.option("--edit", "-e", is_flag=True, help="Opens note in editor")
@click.pass_context
def create(ctx, title, tags, edit):
    store = ctx.obj

    if not validate_title(title):
        click.secho("ERROR: INVALID TITLE!", fg="red", bold=True)
        click.secho(f"REJECTED {title}", fg="red")
        click.secho("Please use only letters, numbers, and spaces", fg="yellow")
        return

    title = clean_title(title)
    slug = slugify(title)

    if tags:
        if not validate_tags(tags):
            click.secho(f"ERROR INVALID TAGS", fg='red', bold=True)
            click.secho(f"REJECTED {tags}", fg="red")
            click.secho("Please use only letters, numbers, and spaces", fg="yellow")
            click.secho("No more than 2 tags allowed!", fg='yellow')
            return

    try:
        store.create_note(title, slug, content="", tags=tags or "")
        store.export_debug_log()
        click.secho(f"Note with name {title} created successfully with slug: {slug} at {store.db_path.absolute()}", fg='green')
        if edit:
            ctx.invoke(edit_note, name=title)
    except sqlite3.IntegrityError:
        click.secho(f"ERROR: A note with slug '{slug}' already exists!", fg="red")
        click.secho("Please provide a unique title", fg='yellow')

@cli.command()
@click.argument("query")
@click.pass_context
def search(ctx, query):
    click.secho(f"searching for {query}", fg="cyan")
    results = ctx.obj.search(query)
    if not results:
        click.secho("No notes found", fg="yellow")
        return

    for title, slug in results:
        click.echo(click.style(f">{title}", fg="white", bold=True) +
                   click.style(f"({slug})", fg="green"))


@cli.command(name='ls')
@click.option("--tag", "-t", default="", help="Filtering notes by tag")
@click.pass_context
def list_notes(ctx, tag):
    store =  ctx.obj

    if tag:
        notes = store.list_notes_by_tag(tag)
    else:
        notes = store.list_notes()

    if not notes:
        click.secho("Your note store is empty", fg='yellow')
        return

    click.secho(f"-----Showing {len(notes)} notes-----", fg='cyan', bold=True)

    for title, slug, tags, updated in notes:
        tag_str = tags.replace(" ", "") if tags else '-'
        date_str = updated.split('T')[0] if updated else 'N/A'

        click.echo(
            click.style(f"Title: {title[:20].ljust(22)}", fg='white', bold=True) +
            click.style(f"Slug: {slug[:15].ljust(17)}", fg='green', bold=True) +
            click.style(f"Tags: {tag_str[:20].ljust(20)}", fg='cyan', bold=True) +
            click.style(f"Date: {date_str}", fg='cyan', bold=True)
        )


@cli.command(name='rm')
@click.argument("name")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation prompt")
@click.pass_context
def delete_note(ctx, name, yes):
    store = ctx.obj
    slug = slugify(name)

    if store.get_content(slug) is None:
        click.secho(f"ERROR note {slug} not found", fg='red')
        return

    if not yes:
        if not click.confirm(f"Are you sure you want to delete {name}??"):
            click.secho("Aborted.")
            return

    if store.delete_note(slug):
        store.export_debug_log()
        click.secho(f"Note named {name} with slug: {slug} deleted successfully", fg='green')
    else:
        click.secho("Something went wrong during deletion", fg='red')


@cli.command(name="retag")
@click.argument("name")
@click.argument("tags")
@click.pass_context
def retag(ctx, name, tags):
    store = ctx.obj
    slug = slugify(name)

    if not validate_tags(tags):
        click.secho(f"ERROR INVALID TAGS", fg='red', bold=True)
        click.secho(f"REJECTED {tags}", fg="red")
        click.secho("Please use only letters, numbers, and spaces", fg="yellow")
        click.secho("No more than 2 tags allowed!", fg='yellow')
        return

    if store.get_content(slug) is None:
        click.secho(f"ERROR note {slug} not found", fg='red')
        return

    store.update_tags(slug, tags)
    click.secho(f"Tags for {name} updated!", fg='green')


@cli.command(name="rename")
@click.argument("name")
@click.argument("new_name")
@click.pass_context
def rename_note(ctx, name, new_name):
    store = ctx.obj
    slug = slugify(name)

    if not validate_title(new_name):
        click.secho("ERROR: INVALID TITLE!", fg="red", bold=True)
        click.secho(f"REJECTED {new_name}", fg="red")
        click.secho("Please use only letters, numbers, and spaces", fg="yellow")
        return

    new_name = clean_title(new_name)
    new_slug = slugify(new_name)

    if store.get_content(slug) is None:
        click.secho(f"ERROR note {slug} not found", fg='red')
        return

    store.rename_note(slug, new_name, new_slug)
    click.secho(f"Title for {name} changed to {new_name}", fg='green')


@cli.command(name="show")
@click.argument("name")
@click.pass_context
def show_notes(ctx, name):
    store = ctx.obj
    slug =  slugify(name)

    content = store.get_content(slug)

    if content is None:
        click.secho(f"ERROR: Note {name} not found", fg='red')
        return
    md = Markdown(content)
    click.secho(f"----- {slug} -----", fg='cyan', bold=True)
    console.print(Padding(md, (1,2,1,2)))