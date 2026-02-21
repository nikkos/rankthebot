import typer

from rankthebot.cli.auth import app as auth_app
from rankthebot.cli.queries import app as queries_app
from rankthebot.cli.report import app as report_app
from rankthebot.cli.scan import scan as scan_command

app = typer.Typer(help="RankTheBot — Track your brand visibility across LLM responses")
app.add_typer(auth_app, name="auth")
app.add_typer(queries_app, name="queries")
app.add_typer(report_app, name="report")
app.command("scan")(scan_command)

if __name__ == "__main__":
    app()
