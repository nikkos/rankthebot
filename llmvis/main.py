import typer

from llmvis.cli.auth import app as auth_app
from llmvis.cli.queries import app as queries_app
from llmvis.cli.report import app as report_app
from llmvis.cli.scan import scan as scan_command

app = typer.Typer(help="LLM Visibility Tracker CLI")
app.add_typer(auth_app, name="auth")
app.add_typer(queries_app, name="queries")
app.add_typer(report_app, name="report")
app.command("scan")(scan_command)

if __name__ == "__main__":
    app()
