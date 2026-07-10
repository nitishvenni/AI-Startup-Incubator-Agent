"""
routes/startup.py - Create, view, and delete startup project routes.
"""

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    current_app,
)
from models.startup import (
    create_startup,
    get_startup_by_id,
    delete_startup,
    update_startup_status,
)
from models.report import create_report, get_report_by_project
from services.watsonx_service import analyze_startup
from utils.helpers import format_datetime, score_label, score_color, industry_icon

startup_bp = Blueprint("startup", __name__)

INDUSTRIES = [
    "Technology", "Healthcare", "Finance", "Education", "E-commerce",
    "Real Estate", "Food & Beverage", "Transportation", "Entertainment",
    "Agriculture", "Energy", "Fashion", "Travel", "Sports", "Other",
]

BUDGETS = [
    "Under $10,000", "$10,000 – $50,000", "$50,000 – $100,000",
    "$100,000 – $500,000", "$500,000 – $1M", "Over $1M",
]

COUNTRIES = [
    "United States", "United Kingdom", "Canada", "Australia", "Germany",
    "France", "India", "China", "Japan", "Brazil", "South Africa",
    "Nigeria", "Kenya", "Singapore", "UAE", "Netherlands", "Sweden",
    "Israel", "South Korea", "Mexico", "Other",
]


@startup_bp.route("/create", methods=["GET", "POST"])
def create():
    """Render the create-startup form and handle submission."""
    if request.method == "POST":
        form = request.form
        data = {
            "startup_name":     form.get("startup_name", "").strip(),
            "founder_name":     form.get("founder_name", "").strip(),
            "country":          form.get("country", "").strip(),
            "industry":         form.get("industry", "").strip(),
            "budget":           form.get("budget", "").strip(),
            "target_audience":  form.get("target_audience", "").strip(),
            "business_goal":    form.get("business_goal", "").strip(),
            "idea_description": form.get("idea_description", "").strip(),
        }

        # Basic validation
        missing = [k for k, v in data.items() if not v]
        if missing:
            flash(f"Please fill in all required fields: {', '.join(missing)}", "danger")
            return render_template(
                "create_startup.html",
                industries=INDUSTRIES,
                budgets=BUDGETS,
                countries=COUNTRIES,
                form_data=form,
            )

        app = current_app._get_current_object()
        project_id = create_startup(app, data)

        # Run AI analysis immediately
        try:
            analysis = analyze_startup(app, data)
            create_report(
                app,
                {
                    "project_id":       project_id,
                    "report_type":      "full_analysis",
                    "content":          analysis["content"],
                    "viability_score":  analysis["viability_score"],
                    "market_score":     analysis["market_score"],
                    "innovation_score": analysis["innovation_score"],
                    "execution_score":  analysis["execution_score"],
                },
            )
            update_startup_status(app, project_id, "analyzed")
            flash("Your startup has been analyzed successfully!", "success")
        except RuntimeError as exc:
            flash(f"Analysis failed: {exc}", "warning")
            update_startup_status(app, project_id, "pending")

        return redirect(url_for("startup.detail", project_id=project_id))

    return render_template(
        "create_startup.html",
        industries=INDUSTRIES,
        budgets=BUDGETS,
        countries=COUNTRIES,
        form_data={},
    )


@startup_bp.route("/<int:project_id>")
def detail(project_id: int):
    """Detail view for a single startup project and its AI report."""
    app = current_app._get_current_object()
    startup = get_startup_by_id(app, project_id)
    if not startup:
        flash("Startup project not found.", "danger")
        return redirect(url_for("main.history"))

    report = get_report_by_project(app, project_id)
    startup["icon"] = industry_icon(startup["industry"])
    startup["created_at_fmt"] = format_datetime(startup["created_at"])

    if report:
        report["viability_label"]   = score_label(report["viability_score"])
        report["viability_color"]   = score_color(report["viability_score"])
        report["market_label"]      = score_label(report["market_score"])
        report["market_color"]      = score_color(report["market_score"])
        report["innovation_label"]  = score_label(report["innovation_score"])
        report["innovation_color"]  = score_color(report["innovation_score"])
        report["execution_label"]   = score_label(report["execution_score"])
        report["execution_color"]   = score_color(report["execution_score"])

    return render_template("detail.html", startup=startup, report=report)


@startup_bp.route("/<int:project_id>/delete", methods=["POST"])
def delete(project_id: int):
    """Hard-delete a project and redirect to history."""
    app = current_app._get_current_object()
    startup = get_startup_by_id(app, project_id)
    if startup:
        delete_startup(app, project_id)
        flash(f"'{startup['startup_name']}' has been deleted.", "info")
    return redirect(url_for("main.history"))


@startup_bp.route("/<int:project_id>/reanalyze", methods=["POST"])
def reanalyze(project_id: int):
    """Re-run the AI analysis for an existing project."""
    app = current_app._get_current_object()
    startup = get_startup_by_id(app, project_id)
    if not startup:
        flash("Project not found.", "danger")
        return redirect(url_for("main.history"))

    try:
        analysis = analyze_startup(app, startup)
        create_report(
            app,
            {
                "project_id":       project_id,
                "report_type":      "full_analysis",
                "content":          analysis["content"],
                "viability_score":  analysis["viability_score"],
                "market_score":     analysis["market_score"],
                "innovation_score": analysis["innovation_score"],
                "execution_score":  analysis["execution_score"],
            },
        )
        update_startup_status(app, project_id, "analyzed")
        flash("Re-analysis complete!", "success")
    except RuntimeError as exc:
        flash(f"Re-analysis failed: {exc}", "warning")

    return redirect(url_for("startup.detail", project_id=project_id))
